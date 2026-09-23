#!/usr/bin/env python3
"""Suite de tests des hooks du template (régression).

Pourquoi : les hooks tournent à CHAQUE action Claude — un hook cassé dégrade en
silence chaque session. Cette suite s'exécute sans dépendance externe (stdlib).

Usage : python3 test/test_hooks.py     (exit 0 = tout vert)
"""
import json, os, py_compile, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
TEAM_HOOKS = ROOT / "plugins" / "agent-teams" / "hooks"  # hooks packagés dans le plugin agent-teams
DOCS = ROOT / ".claude" / "docs"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def run_hook(name, payload, cwd):
    path = HOOKS / name
    if not path.exists():  # hooks livrés par un plugin (ex. teamtask-log.py → agent-teams)
        path = TEAM_HOOKS / name
    exe = ["bash", str(path)] if name.endswith(".sh") else [sys.executable, str(path)]
    return subprocess.run(exe, input=json.dumps(payload), capture_output=True, text=True, cwd=cwd)


def sandbox():
    sb = Path(tempfile.mkdtemp(prefix="hooktest-"))
    (sb / ".claude" / "docs").mkdir(parents=True)
    return sb


# 0. Compilation
print("== compilation ==")
for h in list(HOOKS.glob("*.py")) + list(TEAM_HOOKS.glob("*.py")):
    try:
        py_compile.compile(str(h), doraise=True); ok(f"compile {h.name}", True)
    except py_compile.PyCompileError as e:
        ok(f"compile {h.name}: {e}", False)

# 1. precompact → cache non-versionné PAR-SESSION, HANDOFF intact, overwrite, trigger top-level
print("\n== precompact-snapshot-handoff ==")
sb = sandbox()
ho = sb / ".claude/docs/HANDOFF.md"; ho.write_text("# HANDOFF\nétat initial\n")
size0 = ho.stat().st_size
# 5 compactions, MÊME session → overwrite d'un unique fichier par-session (pas d'append/bloat)
for _ in range(5):
    run_hook("precompact-snapshot-handoff.py",
             {"session_id": "sess-A", "transcript_path": "", "cwd": str(sb),
              "trigger": "auto"}, sb)
cache_a = sb / ".claude/.cache/handoff-snapshot-sess-A.md"
ok("HANDOFF.md versionné NON modifié", ho.stat().st_size == size0)
ok("snapshot écrit en cache (par-session)", cache_a.exists())
ok("cache = 1 seul snapshot (overwrite)", cache_a.exists() and cache_a.read_text().count("📸 Auto-snapshot") == 1)
# isolation multi-agent : un autre session_id → un AUTRE fichier (pas d'écrasement croisé)
run_hook("precompact-snapshot-handoff.py",
         {"session_id": "sess-B", "transcript_path": "", "cwd": str(sb), "trigger": "auto"}, sb)
ok("snapshot par-session isolé (pas de collision teammates)",
   (sb / ".claude/.cache/handoff-snapshot-sess-B.md").exists())
# régression bug trigger : "manual" lu au TOP-LEVEL (pas dans tool_input)
run_hook("precompact-snapshot-handoff.py",
         {"session_id": "sess-M", "transcript_path": "", "cwd": str(sb), "trigger": "manual"}, sb)
snap_m = sb / ".claude/.cache/handoff-snapshot-sess-M.md"
ok("trigger 'manual' top-level rendu dans le snapshot",
   snap_m.exists() and "(manual)" in snap_m.read_text())
# garde-fou : l'ANCIEN schéma (tool_input.trigger) ne doit plus être lu → fallback 'auto'
run_hook("precompact-snapshot-handoff.py",
         {"session_id": "sess-OLD", "transcript_path": "", "cwd": str(sb),
          "tool_input": {"trigger": "manual"}}, sb)
snap_old = sb / ".claude/.cache/handoff-snapshot-sess-OLD.md"
ok("ancien schéma tool_input.trigger ignoré → fallback 'auto'",
   snap_old.exists() and "(auto)" in snap_old.read_text())
shutil.rmtree(sb, ignore_errors=True)

# 2. sessionstart → ré-injecte depuis le cache ; pas de marker → silencieux
print("\n== sessionstart-inject-handoff ==")
sb = sandbox()
(sb / ".claude/docs/HANDOFF.md").write_text("# HANDOFF\n")
run_hook("precompact-snapshot-handoff.py",
         {"session_id": "loop", "transcript_path": "", "cwd": str(sb),
          "trigger": "manual"}, sb)
r = run_hook("sessionstart-inject-handoff.py", {"session_id": "loop", "cwd": str(sb)}, sb)
ok("ré-injection après compaction", "Re-injection post-compaction" in r.stdout)
r2 = run_hook("sessionstart-inject-handoff.py", {"session_id": "absent", "cwd": str(sb)}, sb)
ok("pas de marker → exit 0 silencieux", r2.returncode == 0 and r2.stdout.strip() == "")
shutil.rmtree(sb, ignore_errors=True)

# 3. pretooluse-inject-codemap → gotchas ciblés 1×/(session, fichier) — v1.5.0 : plus de réinjection
#    du couplage (doublon de code-map.md, déjà en contexte) ni de liste fixe src/tests/lib/app
#    (mesuré 2026-09-08 : la version < 1.4 réinjectait ~2,2k tokens à CHAQUE Edit)
print("\n== pretooluse-inject-codemap ==")
GOTCHAS = """# Gotchas

## Globaux

- ⚠️ montants en centimes int partout

## Par zone

- ⚠️ `src/sync/notion.py` — l'API renvoie 200 même en erreur
- ⚠️ `src/api/` — le cache est invalidé par tout write
  (suite indentée de l'entrée api)

### src/jobs/

- ⚠️ le scheduler ignore les jobs sans `retry`
"""


def inject(sb, path, session="S1", tool="Edit"):
    r = run_hook("pretooluse-inject-codemap.py",
                 {"session_id": session, "tool_name": tool, "tool_input": {"file_path": str(sb / path)}, "cwd": str(sb)}, sb)
    if not r.stdout.strip():
        return ""
    return json.loads(r.stdout).get("hookSpecificOutput", {}).get("additionalContext", "")


sb = sandbox()
shutil.copy2(DOCS / "code-map.md", sb / ".claude/docs/code-map.md")
(sb / ".claude/docs/code-map-gotchas.md").write_text(GOTCHAS, encoding="utf-8")
i1 = inject(sb, "src/sync/notion.py")
ok("1re édition : couplage NON réinjecté (déjà en contexte via code-map.md)",
   i1 != "" and "Règles de couplage" not in i1 and "Intention" not in i1)
ok("1re édition : gotcha ciblé (notion.py) + global injectés, gotchas des autres zones NON",
   "renvoie 200" in i1 and "centimes" in i1 and "invalidé" not in i1 and "scheduler" not in i1)
ok("marker par session écrit dans .claude/.cache/", (sb / ".claude/.cache/codemap-injected-S1.json").is_file())
ok("même fichier, même session → aucune ré-injection", inject(sb, "src/sync/notion.py") == "")
i3 = inject(sb, "src/api/http.py")
ok("autre fichier, même session : gotcha de sa zone (`src/api/` + suite indentée) seulement",
   "invalidé" in i3 and "suite indentée" in i3 and "Règles de couplage" not in i3 and "renvoie 200" not in i3)
i4 = inject(sb, "src/jobs/nightly.py")
ok("heading `### src/jobs/` cible ses entrées", "scheduler" in i4)
i5 = inject(sb, "src/other/x.py")
ok("fichier sans gotcha ciblé : seuls les Globaux (1×/fichier), aucune zone",
   "centimes" in i5 and "Règles de couplage" not in i5 and "renvoie 200" not in i5 and "invalidé" not in i5)
ok("nouvelle session → gotchas du fichier ré-injectés", "renvoie 200" in inject(sb, "src/sync/notion.py", session="S2"))
ok("pas d'injection pour un .md", inject(sb, "src/README.md") == "")
ok("pas d'injection pour la config (.json/.yaml/.toml)", inject(sb, "backend/config.yaml") == "")
it = inject(sb, "scripts/tool.py")
ok("hors src/tests/lib/app (scripts/) : Globaux injectés — plus de liste fixe de dossiers",
   "centimes" in it and "renvoie 200" not in it)
ok("fichier sous .claude/ (méthode) → aucune injection", inject(sb, ".claude/hooks/x.py") == "")
r_out = run_hook("pretooluse-inject-codemap.py",
                 {"session_id": "S1", "tool_name": "Edit", "tool_input": {"file_path": "/elsewhere/src/a.py"},
                  "cwd": str(sb)}, sb)
ok("fichier hors projet (même sous un src/) → aucune injection", r_out.stdout.strip() == "")
# ré-armement post-compaction : SessionStart(compact) efface le marker
run_hook("sessionstart-inject-handoff.py", {"session_id": "S1", "source": "compact", "cwd": str(sb)}, sb)
ok("après compaction : marker effacé → gotchas ré-injectés à la prochaine édition",
   not (sb / ".claude/.cache/codemap-injected-S1.json").exists() and "renvoie 200" in inject(sb, "src/sync/notion.py"))
shutil.rmtree(sb, ignore_errors=True)

# fallback projet < 1.4 : gotchas encore dans code-map.md § Gotchas → ciblage identique
sb = sandbox()
(sb / ".claude/docs/code-map.md").write_text(
    "# CM\n\n## Règles de couplage\n\n- ❌ jamais A → B\n\n## Gotchas (pièges non évidents)\n\n"
    "- ⚠️ `src/sync/notion.py` — 200 même en erreur\n- ⚠️ `src/api/` — cache invalidé\n", encoding="utf-8")
i = inject(sb, "src/sync/notion.py")
ok("projet < 1.4 (gotchas dans code-map.md) : ciblage appliqué quand même",
   "200 même en erreur" in i and "cache invalidé" not in i and "Règles de couplage" not in i)
ok("taille d'une injection bornée (≤ 2,5k chars + en-tête)", len(i) < 3000)
ok("sans Globaux, fichier sans gotcha ciblé → silence total", inject(sb, "src/other/y.py") == "")
big = "## Globaux\n\n" + "".join(f"- ⚠️ piège global numéro {n} " + "x" * 80 + "\n" for n in range(200))
(sb / ".claude/docs/code-map-gotchas.md").write_text(big, encoding="utf-8")
ok("gotchas volumineux → injection plafonnée", len(inject(sb, "src/big.py", session="S9")) < 3000)
shutil.rmtree(sb, ignore_errors=True)

# 4. posttooluse-growth-detection → flag API_KEY
print("\n== posttooluse-growth-detection ==")
sb = sandbox()
r = run_hook("posttooluse-growth-detection.py",
             {"tool_name": "Write", "tool_input": {"file_path": str(sb / "src/conf.py"),
              "content": "API_KEY = 'secret'  # OAuth token"}, "cwd": str(sb)}, sb)
gs = sb / ".claude/.growth-suggestions.md"
ok("growth-suggestions créé sur trigger credentials", gs.exists())
ok("systemMessage émis", "systemMessage" in r.stdout)
r2 = run_hook("posttooluse-growth-detection.py",
              {"tool_name": "Write", "tool_input": {"file_path": str(sb / "src/plain.py"),
               "content": "def add(a, b):\n    return a + b\n"}, "cwd": str(sb)}, sb)
ok("pas de flag sur code anodin", r2.stdout.strip() == "")
# MultiEdit : le contenu est dans edits[].new_string, pas content/new_string
r3 = run_hook("posttooluse-growth-detection.py",
              {"tool_name": "MultiEdit", "tool_input": {"file_path": str(sb / "src/deploy.py"),
               "edits": [{"old_string": "x", "new_string": "run production rollback"}]}, "cwd": str(sb)}, sb)
ok("MultiEdit scanné (edits[].new_string)", "systemMessage" in r3.stdout)
# dédup sans minute : 2e write même source/trigger → pas de nouvelle entrée dupliquée
before = (sb / ".claude/.growth-suggestions.md").read_text().count("src/conf.py")
run_hook("posttooluse-growth-detection.py",
         {"tool_name": "Write", "tool_input": {"file_path": str(sb / "src/conf.py"),
          "content": "API_KEY = 'secret2'"}, "cwd": str(sb)}, sb)
after = (sb / ".claude/.growth-suggestions.md").read_text().count("src/conf.py")
ok("dédup par (source,message) sans timestamp → pas de doublon", before == after == 1)
# auto-référence : trier .growth-suggestions.md (plein de mots triggers) ne doit RIEN regénérer
# (vécu 2026-09-02 sur projet généré : le tri du fichier re-flaggait « credentials »/« prod »
# dans les lignes qu'on barrait → boucle)
snap = gs.read_text()
r4 = run_hook("posttooluse-growth-detection.py",
              {"tool_name": "Edit", "tool_input": {"file_path": str(gs),
               "new_string": "- ~~credentials API_KEY OAuth~~ traité\n- ~~deploy production~~ traité\n"},
               "cwd": str(sb)}, sb)
ok("s'ignore lui-même (tri de .growth-suggestions.md → aucun flag, fichier inchangé)",
   r4.stdout.strip() == "" and gs.read_text() == snap)
# guard large v1.3.2 : éditer une rule/skill sous .claude/ (qui parle de credentials/prod)
# ne doit pas flagger — seul le code projet compte
r5 = run_hook("posttooluse-growth-detection.py",
              {"tool_name": "Write", "tool_input": {"file_path": str(sb / ".claude/rules/securite.md"),
               "content": "Jamais de credentials API_KEY en clair. Deploy production via CI."},
               "cwd": str(sb)}, sb)
ok("tout .claude/ ignoré (rule parlant de credentials → aucun flag)",
   r5.stdout.strip() == "" and gs.read_text() == snap)
shutil.rmtree(sb, ignore_errors=True)

# 5. stop-handoff-reminder.sh → rappel si HANDOFF vieux + changements git
print("\n== stop-handoff-reminder ==")
sb = sandbox()
ho = sb / ".claude/docs/HANDOFF.md"; ho.write_text("# HANDOFF\n")
# fresh → pas de rappel
r = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb)}, sb)
ok("HANDOFF frais → pas de rappel", r.stdout.strip() == "")
# vieux (>24h) + repo git avec changement → rappel
has_git = shutil.which("git") is not None
if has_git:
    subprocess.run(["git", "init", "-q"], cwd=sb)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=sb)
    subprocess.run(["git", "config", "user.name", "t"], cwd=sb)
    (sb / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=sb)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=sb)
    (sb / "f.txt").write_text("y")  # changement non commité
    old = time.time() - 48 * 3600
    os.utime(ho, (old, old))
    r2 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "AGE1"}, sb)
    ok("HANDOFF vieux + git dirty → rappel", "HANDOFF" in r2.stdout)
    r2b = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "AGE1"}, sb)
    ok("même session → rappel d'âge UNE seule fois (pas à chaque tour)", r2b.stdout.strip() == "")
    r2c = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "AGE2"}, sb)
    ok("autre session → rappel d'âge à nouveau", "HANDOFF" in r2c.stdout)
    # gate lead-only : un teammate identifié (agent_type≠lead) ne rappelle PAS
    r3 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "agent_type": "Explore"}, sb)
    ok("teammate (agent_type≠lead) → pas de rappel", r3.stdout.strip() == "")
    # levier env : CLAUDE_HANDOFF_REMINDER=off coupe le rappel (cas sessions teammate top-level)
    r4 = subprocess.run(["bash", str(HOOKS / "stop-handoff-reminder.sh")],
                        input=json.dumps({"cwd": str(sb)}), capture_output=True, text=True,
                        cwd=sb, env=dict(os.environ, CLAUDE_HANDOFF_REMINDER="off"))
    ok("CLAUDE_HANDOFF_REMINDER=off → pas de rappel", r4.stdout.strip() == "")
    # projet archivé (/archive-projet) : marqueur .claude/archived présent → silence,
    # même avec HANDOFF vieux + git dirty
    (sb / ".claude/archived").write_text("archived: 2026-09-02\n")
    r5 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb)}, sb)
    ok("projet archivé (.claude/archived) → pas de rappel", r5.stdout.strip() == "")
    (sb / ".claude/archived").unlink()
else:
    ok("git absent (skip test rappel)", True)
# garde-fou TAILLE (v1.4.1) : HANDOFF > 12 000 octets → rappel même s'il est FRAIS, une fois par session
ho.write_text("# HANDOFF\n" + ("## 15/09 — preuve empilée\n\n- bla bla bla bla bla\n" * 400))
os.utime(ho, None)
r6 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "S1"}, sb)
ok("HANDOFF > 12 Ko (frais) → rappel taille avec Ko/lignes", "📏" in r6.stdout and "Ko" in r6.stdout and "HANDOFF-journal" in r6.stdout)
r7 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "S1"}, sb)
ok("même session → rappel taille une seule fois", r7.stdout.strip() == "")
r8 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "session_id": "S2"}, sb)
ok("autre session → rappel taille à nouveau", "📏" in r8.stdout)
r9 = subprocess.run(["bash", str(HOOKS / "stop-handoff-reminder.sh")],
                    input=json.dumps({"cwd": str(sb), "session_id": "S3"}), capture_output=True, text=True,
                    cwd=sb, env=dict(os.environ, CLAUDE_HANDOFF_MAX_BYTES="0"))
ok("CLAUDE_HANDOFF_MAX_BYTES=0 → garde-fou taille désactivé", "📏" not in r9.stdout)
ho.write_text("# HANDOFF\n")
shutil.rmtree(sb, ignore_errors=True)

# 6. sessionend-snapshot → filet fin de session (cache, overwrite, reason rendu)
print("\n== sessionend-snapshot ==")
sb = sandbox()
(sb / ".claude/docs/HANDOFF.md").write_text("# HANDOFF\n")
for _ in range(2):
    run_hook("sessionend-snapshot.py",
             {"session_id": "end-A", "transcript_path": "", "cwd": str(sb), "reason": "other"}, sb)
snap = sb / ".claude/.cache/session-end-snapshot.md"
ok("snapshot fin de session écrit en cache", snap.exists())
ok("overwrite (1 seul snapshot)", snap.exists() and snap.read_text().count("📸 Auto-snapshot") == 1)
ok("reason rendu dans le header", snap.exists() and "fin de session (other)" in snap.read_text())

# 7. sessionstart source=startup → injection du filet SI plus frais que HANDOFF, consommé ensuite
print("\n== sessionstart-inject (source=startup, filet fin de session) ==")
ho = sb / ".claude/docs/HANDOFF.md"
old = time.time() - 3600
os.utime(ho, (old, old))  # HANDOFF plus vieux que le snapshot → /handoff oublié
r = run_hook("sessionstart-inject-handoff.py",
             {"session_id": "new-sess", "cwd": str(sb), "source": "startup"}, sb)
ok("snapshot plus frais → injection filet", "Filet mémoire" in r.stdout)
ok("snapshot consommé après injection", not snap.exists())
# cas /handoff fait (HANDOFF plus frais) → silencieux + purge quand même
run_hook("sessionend-snapshot.py",
         {"session_id": "end-B", "transcript_path": "", "cwd": str(sb), "reason": "logout"}, sb)
future = time.time() + 60
os.utime(ho, (future, future))
r2 = run_hook("sessionstart-inject-handoff.py",
              {"session_id": "n2", "cwd": str(sb), "source": "startup"}, sb)
ok("HANDOFF plus frais → pas d'injection", r2.stdout.strip() == "")
ok("snapshot purgé quand même (consume-once)", not snap.exists())
r3 = run_hook("sessionstart-inject-handoff.py",
              {"session_id": "n3", "cwd": str(sb), "source": "startup"}, sb)
ok("pas de snapshot → exit 0 silencieux", r3.returncode == 0 and r3.stdout.strip() == "")
# filet BUDGET (v1.4.1) : context-budget.py présent + surface auto-chargée > 25k tok → avertissement
BUDGET = ROOT / ".claude/skills/doc-health/scripts/context-budget.py"
(sb / ".claude/skills/doc-health/scripts").mkdir(parents=True, exist_ok=True)
shutil.copy2(BUDGET, sb / ".claude/skills/doc-health/scripts/context-budget.py")
(sb / "CLAUDE.md").write_text("# P\n\n- Reprise : @.claude/docs/HANDOFF.md\n")
ho.write_text("# HANDOFF\n" + ("## 15/09 — section empilée\n\n- bla bla bla bla\n" * 1500))  # ≈ 60 Ko ≈ 30k tok est.
r4 = run_hook("sessionstart-inject-handoff.py", {"session_id": "n4", "cwd": str(sb), "source": "startup"}, sb)
ok("surface auto-chargée > seuil → avertissement budget avec le coupable (HANDOFF) et le remède",
   "Budget de contexte dépassé" in r4.stdout and "HANDOFF.md" in r4.stdout and "journal" in r4.stdout.lower())
ho.write_text("# HANDOFF\ncourt\n")
r4b = run_hook("sessionstart-inject-handoff.py", {"session_id": "n5", "cwd": str(sb), "source": "startup"}, sb)
ok("surface sous le seuil → silence", r4b.stdout.strip() == "")
ho.write_text("# HANDOFF\n" + ("x" * 70000) + "\n")
r4c = subprocess.run([sys.executable, str(HOOKS / "sessionstart-inject-handoff.py")],
                     input=json.dumps({"session_id": "n6", "cwd": str(sb), "source": "startup"}),
                     capture_output=True, text=True, cwd=sb, env=dict(os.environ, CLAUDE_CONTEXT_BUDGET_MAX="0"))
ok("CLAUDE_CONTEXT_BUDGET_MAX=0 → filet budget désactivé", r4c.stdout.strip() == "")
shutil.rmtree(sb / ".claude/skills", ignore_errors=True)
ho.write_text("# HANDOFF\n")
# routing : source="compact" → flux marker (comportement historique préservé)
run_hook("precompact-snapshot-handoff.py",
         {"session_id": "cmp", "transcript_path": "", "cwd": str(sb), "trigger": "auto"}, sb)
r5 = run_hook("sessionstart-inject-handoff.py",
              {"session_id": "cmp", "cwd": str(sb), "source": "compact"}, sb)
ok("source=compact → flux marker (ré-injection)", "Re-injection post-compaction" in r5.stdout)
shutil.rmtree(sb, ignore_errors=True)

# 7b. SÉQUENCES RÉELLES (v1.5.0) — l'ordre des événements tel que Claude Code les émet.
#     Bug historique : SessionEnd passe TOUJOURS après /handoff → le filet était toujours « plus
#     frais » que HANDOFF.md → fausse alerte « fermée sans /handoff » à CHAQUE démarrage. Les tests
#     unitaires ne le voyaient pas (mtime de HANDOFF forcé dans le futur, ordre impossible en vrai).
print("\n== séquences réelles startup → travail → SessionEnd → startup ==")
if shutil.which("git"):
    sb = sandbox()
    ho = sb / ".claude/docs/HANDOFF.md"; ho.write_text("# HANDOFF\nv0\n")
    for c in (["git", "init", "-q"], ["git", "config", "user.email", "t@t.t"], ["git", "config", "user.name", "t"]):
        subprocess.run(c, cwd=sb)
    (sb / "app.py").write_text("print(1)\n")
    subprocess.run(["git", "add", "-A"], cwd=sb); subprocess.run(["git", "commit", "-qm", "init"], cwd=sb)
    net = sb / ".claude/.cache/session-end-snapshot.md"

    def start(sid, source="startup"):
        return run_hook("sessionstart-inject-handoff.py", {"session_id": sid, "cwd": str(sb), "source": source}, sb)

    def end(sid, reason="prompt_input_exit", transcript=""):
        return run_hook("sessionend-snapshot.py",
                        {"session_id": sid, "transcript_path": transcript, "cwd": str(sb), "reason": reason}, sb)

    # A. code modifié + /handoff fait → pas de filet → démarrage suivant silencieux
    start("A"); time.sleep(0.05)
    (sb / "app.py").write_text("print(2)\n"); ho.write_text("# HANDOFF\nv1 (/handoff)\n")
    end("A")
    ok("A. /handoff fait pendant la session → aucun filet écrit", not net.exists())
    rB = start("B")
    ok("A. démarrage suivant : AUCUNE alerte « fermée sans /handoff » (bug v1.4)", "Filet mémoire" not in rB.stdout)
    ok("A. marqueur de début de session consommé au SessionEnd", not (sb / ".claude/.cache/session-start-A.json").exists())
    # B. code modifié SANS /handoff → filet écrit → injecté au démarrage suivant puis consommé
    time.sleep(0.05); (sb / "app.py").write_text("print(3)\n")
    end("B")
    ok("B. trace git sans /handoff → filet écrit", net.exists())
    rC = start("C")
    ok("B. démarrage suivant : filet injecté", "Filet mémoire" in rC.stdout)
    ok("B. filet consommé (jamais réinjecté deux fois)", not net.exists())
    # C. session sans trace git (question, lecture) → pas de filet
    end("C")
    ok("C. session sans trace git → aucun filet", not net.exists())
    # D. un filet périmé est supprimé quand la session suivante fait /handoff
    start("D"); (sb / "app.py").write_text("print(4)\n"); end("D")
    ok("D. filet posé (préparation)", net.exists())
    start("E"); time.sleep(0.05); ho.write_text("# HANDOFF\nv2 (/handoff)\n"); end("E")
    ok("D. /handoff dans la session suivante → filet périmé supprimé", not net.exists())
    # E. resume / clear : marqueur posé, rien d'injecté
    rR = start("R", source="resume")
    ok("E. resume → marqueur de début posé, aucune injection",
       (sb / ".claude/.cache/session-start-R.json").is_file() and rR.stdout.strip() == "")
    rCl = start("CL", source="clear")
    ok("E. clear → marqueur de début posé, aucune injection",
       (sb / ".claude/.cache/session-start-CL.json").is_file() and rCl.stdout.strip() == "")
    # F. sans marqueur (hook SessionStart absent) → repli sur la 1re date du transcript
    tr = sb / "t.jsonl"
    tr.write_text(json.dumps({"type": "user", "timestamp": "2020-01-01T00:00:00.000Z",
                              "message": {"role": "user", "content": "hello"}}) + "\n")
    (sb / "app.py").write_text("print(5)\n"); ho.write_text("# HANDOFF\nv3\n")
    end("NOMARK", transcript=str(tr))
    ok("F. sans marqueur : début lu dans le transcript → /handoff détecté, pas de filet", not net.exists())
    shutil.rmtree(sb, ignore_errors=True)
else:
    ok("git absent (skip séquences)", True)

# 7c. Extraction des messages HUMAINS depuis un transcript réaliste (v1.5.0) — avant : 3 chaînes
#     vides en PreCompact (tool_result) et « caveat / /exit / Goodbye! » en SessionEnd.
print("\n== snapshot_common : messages humains (fixture transcript réaliste) ==")
sys.path.insert(0, str(HOOKS))
import snapshot_common  # noqa: E402
fx = Path(tempfile.mkdtemp(prefix="transcript-")) / "t.jsonl"
entries = [
    {"type": "user", "timestamp": "2026-09-23T08:00:00.000Z", "message": {"role": "user", "content": "ajoute la pagination à l'API"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]}},
    {"type": "user", "toolUseResult": {"stdout": "x"}, "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}},
    {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "y"}]}},
    {"type": "user", "isMeta": True, "message": {"role": "user", "content": "Caveat: meta"}},
    {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "et garde le curseur opaque"}]}},
    {"type": "user", "message": {"role": "user", "content": "<local-command-caveat>Caveat: The messages below…</local-command-caveat>"}},
    {"type": "user", "message": {"role": "user", "content": "<command-name>/exit</command-name>\n<command-message>exit</command-message>"}},
    {"type": "user", "message": {"role": "user", "content": "<local-command-stdout>Goodbye!</local-command-stdout>"}},
    {"type": "user", "message": {"role": "user", "content": "<system-reminder>rappel</system-reminder>"}},
    {"type": "user", "message": {"role": "user", "content": "[Request interrupted by user]"}},
]
fx.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n{json cassé\n", encoding="utf-8")
msgs = snapshot_common.extract_last_user_messages(str(fx))
ok("seuls les messages humains sont gardés (ni tool_result, ni méta, ni /exit, ni rappels)",
   msgs == ["ajoute la pagination à l'API", "et garde le curseur opaque"])
ok("aucune chaîne vide dans les extraits", all(m.strip() for m in msgs))
ok("début de session lu dans le transcript",
   abs(snapshot_common.transcript_started_at(str(fx)) - 1790150400.0) < 1)
ok("transcript absent → [] sans exception", snapshot_common.extract_last_user_messages("/nonexistent.jsonl") == [])
shutil.rmtree(fx.parent, ignore_errors=True)

# 7d. Purge du cache par-session au démarrage (> 7 jours) — sinon 1 fichier/session s'accumule
print("\n== purge du cache par-session ==")
sb = sandbox()
cache = sb / ".claude/.cache"; cache.mkdir(parents=True)
old_f = [cache / n for n in ("codemap-injected-OLD.json", "handoff-age-warned-OLD", "session-start-OLD.json",
                             "handoff-snapshot-OLD.md", "handoff-size-warned-OLD")]
for f in old_f:
    f.write_text("x"); t_old = time.time() - 10 * 86400; os.utime(f, (t_old, t_old))
fresh = cache / "codemap-injected-NEW.json"; fresh.write_text("{}")
keep = cache / "team-progress.log"; keep.write_text("x"); os.utime(keep, (time.time() - 30 * 86400,) * 2)
run_hook("sessionstart-inject-handoff.py", {"session_id": "P", "cwd": str(sb), "source": "startup"}, sb)
ok("fichiers par-session > 7 j purgés au démarrage", not any(f.exists() for f in old_f))
ok("fichiers récents conservés", fresh.exists())
ok("fichiers hors motifs par-session conservés (team-progress.log)", keep.exists())
shutil.rmtree(sb, ignore_errors=True)

# 8. teamtask-log → 1 ligne JSON/événement, append, jamais bloquant
print("\n== teamtask-log ==")
sb = sandbox()
r = run_hook("teamtask-log.py",
             {"hook_event_name": "TaskCompleted", "cwd": str(sb),
              "task": {"id": "3", "subject": "Créer API", "status": "completed"}}, sb)
lg = sb / ".claude/.cache/team-progress.log"
ok("TaskCompleted loggé", lg.exists() and "TaskCompleted" in lg.read_text())
ok("champs task_* extraits", lg.exists() and '"task_subject": "Créer API"' in lg.read_text())
run_hook("teamtask-log.py",
         {"hook_event_name": "TeammateIdle", "cwd": str(sb), "teammate_name": "front-end"}, sb)
ok("append (2 lignes, 1 par événement)", lg.exists() and len(lg.read_text().strip().splitlines()) == 2)
ok("exit 0 (jamais bloquant)", r.returncode == 0)
r4 = run_hook("teamtask-log.py", {"hook_event_name": "TaskCreated", "cwd": "/nonexistent-dir-xyz"}, sb)
ok("cwd inexistant → exit 0 silencieux", r4.returncode == 0 and r4.stdout.strip() == "")
shutil.rmtree(sb, ignore_errors=True)

print(f"\n{'🎉 TOUS LES HOOKS OK' if FAIL == 0 else '⚠️  ÉCHEC'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
