#!/usr/bin/env python3
"""Tests de /upgrade-template (upgrade.py) — mise à jour des projets générés, merge 3 voies.

Les projets sont générés comme en vrai : `git archive <tag>` du dépôt template → render.py +
cleanup-for-type.py DE CETTE VERSION (fixture « caisse ») → commit ; puis upgrade vers l'arbre de
travail (WORKTREE = la version en cours de développement).

Garde-fous testés :
  1. projet non modifié, TOUTES les versions taguées (v0.16.0 → dernière) × python-app : upgrade =
     octet pour octet une init fraîche de la cible, code 0, idempotent
  2. personnalisations : allow-rule / hook / skill maison conservés, retraits volontaires respectés,
     fusion texte non conflictuelle appliquée, conflit → fichier du projet GARDÉ + version cible déposée
  3. projet < 1.4 qui a grossi (journal HANDOFF, gotchas, ROADMAP en @) : migration de la doc,
     aucun contenu perdu, budget de contexte revenu sous le seuil
  4. profils déduits (script-jetable, web-app) et lock écrit
  5. dry-run sans écriture · arbre git sale refusé · équipe d'agents active préservée

Usage : python3 test/test_upgrade.py [--quick]   (exit 0 = tout vert ; --quick = 4 versions au lieu de toutes)
Prérequis : les tags vX.Y.Z du dépôt (en CI : checkout avec fetch-depth: 0).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPGRADE = ROOT / ".claude" / "skills" / "upgrade-template" / "scripts" / "upgrade.py"
BUDGET = ROOT / ".claude" / "skills" / "doc-health" / "scripts" / "context-budget.py"
EXCLUDE_TOP = {"EXAMPLES", "test", ".github", ".git", "plugins", ".claude-plugin"}
VARS = {
    "PROJECT_NAME": "Caisse Rapide", "CLIENT_NAME": "Boulangerie Martin",
    "PROJECT_FOLDER": "caisse-rapide", "NOM_DECIDEUR": "Sophie Martin",
    "EMAIL_DECIDEUR": "sophie@boulangerie-martin.fr", "TON_NOM": "Julien Leroy",
    "TON_EMAIL": "julien@example.org", "COMMANDE_INSTALL": "pip install -e .[dev]",
    "COMMANDE_RUN": "python -m caisse", "COMMANDE_TESTS": "pytest -q",
}
GIT = ["git", "-c", "user.email=t@t.t", "-c", "user.name=t"]
PASS = FAIL = 0
QUICK = "--quick" in sys.argv


def ok(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def sh(args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{args}\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return r


def tags():
    out = sh(["git", "-C", str(ROOT), "tag", "--list", "v*"]).stdout.split()
    vs = [t for t in out if re.fullmatch(r"v\d+\.\d+\.\d+", t)
          and (ROOT / ".git").exists()
          and sh(["git", "-C", str(ROOT), "cat-file", "-e", f"{t}:.claude/template-version"], check=False).returncode == 0]
    return sorted(vs, key=lambda t: tuple(int(x) for x in t[1:].split(".")))


def materialize(ref: str, dest: Path):
    dest.mkdir(parents=True)
    if ref == "WORKTREE":
        for child in ROOT.iterdir():
            if child.name in EXCLUDE_TOP:
                continue
            if child.is_dir():
                shutil.copytree(child, dest / child.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".cache"))
            else:
                shutil.copy2(child, dest / child.name)
        return
    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", ref], capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar.stdout, check=True)
    for d in EXCLUDE_TOP:
        p = dest / d
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else (p.unlink() if p.exists() else None)


def init_project(ref: str, profile: str, dest: Path, extra=None) -> Path:
    """Init réelle d'un projet à la version `ref` (scripts de CETTE version), commitée."""
    materialize(ref, dest)
    if extra:
        extra(dest)
    sh(["git", "init", "-q"], cwd=dest)
    sh(GIT + ["add", "-A"], cwd=dest)
    sh(GIT + ["commit", "-qm", "snapshot pre-init"], cwd=dest)
    vf = dest.parent / f"vars-{dest.name}.json"
    vf.write_text(json.dumps(VARS), encoding="utf-8")
    scripts = dest / ".claude/skills/init-from-template/scripts"
    sh([sys.executable, str(scripts / "render.py"), "--vars", str(vf), "--root", str(dest)])
    sh([sys.executable, str(scripts / "cleanup-for-type.py"), "--type", profile, "--root", str(dest)])
    commit(dest, f"init {ref} {profile}")
    return dest


def commit(root: Path, msg: str):
    sh(GIT + ["add", "-A"], cwd=root)
    sh(GIT + ["commit", "-qm", msg, "--allow-empty"], cwd=root)


def upgrade(project: Path, *extra):
    # Réglages utilisateur isolés (CLAUDE_CONFIG_DIR) : un plugin agent-teams activé en user-scope
    # sur la machine du testeur ne doit pas changer le résultat.
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(TMP / "claude-config"))
    r = subprocess.run([sys.executable, str(UPGRADE), "--project", str(project), "--template", str(ROOT),
                        "--to", "WORKTREE", *extra], capture_output=True, text=True, env=env)
    return r


def upgrade_json(project: Path, *extra):
    r = upgrade(project, "--json", *extra)
    try:
        return r.returncode, json.loads(r.stdout)
    except ValueError:
        print(r.stdout[-1500:], r.stderr[-1500:])
        return r.returncode, {}


def method_files(root: Path):
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel.startswith((".git/", ".claude/.cache/", ".claude/docs/")) \
                or "__pycache__" in rel or rel in (".claude/template-lock.json",):
            continue
        if rel.startswith(".claude/") or rel in ("CLAUDE.md", ".gitignore", ".pre-commit-config.yaml",
                                                 "workflows/README.md"):
            out[rel] = p.read_bytes()
    return out


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file() and ".git" not in x.relative_to(root).parts):
        h.update(p.relative_to(root).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


TMP = Path(tempfile.mkdtemp(prefix="test-upgrade-"))
FRESH = {}


def fresh(profile: str) -> Path:
    if profile not in FRESH:
        FRESH[profile] = init_project("WORKTREE", profile, TMP / f"fresh-{profile}")
    return FRESH[profile]


try:
    TAGS = tags()
    if not TAGS:
        print("⚠️  aucun tag vX.Y.Z (checkout sans historique ?) — en CI : actions/checkout fetch-depth: 0")
        sys.exit(1)
    target_v = (ROOT / ".claude/template-version").read_text(encoding="utf-8").strip()

    # ── 1. Projets non modifiés, toutes versions → octet pour octet une init fraîche ────────────
    print(f"== 1. projet non modifié, versions taguées → {target_v} (python-app) ==")
    olds = [t for t in TAGS if t != f"v{target_v}"]
    if QUICK:
        olds = [t for t in olds if t in ("v0.16.0", "v1.0.0", "v1.3.3", olds[-1])]
    ref = method_files(fresh("python-app"))
    for t in olds:
        p = init_project(t, "python-app", TMP / f"clean-{t}")
        rc, rep = upgrade_json(p)
        got = method_files(p)
        diff = sorted(set(ref) ^ set(got)) + sorted(k for k in set(ref) & set(got) if ref[k] != got[k])
        ok(f"{t} → {target_v} : code 0, aucun conflit, = init fraîche octet pour octet"
           + (f" (écarts : {diff[:4]})" if diff else ""),
           rc == 0 and not rep.get("conflicts") and not diff)
        if t == olds[-1]:
            rc2, rep2 = upgrade_json(p, "--allow-dirty")
            ok("2e passage : « à jour », rien d'écrit", rc2 == 0 and rep2.get("status") == "à jour")
            lock = json.loads((p / ".claude/template-lock.json").read_text(encoding="utf-8"))
            ok("lock écrit : version cible + profil, sans variables d'init (PII)",
               lock.get("version") == target_v and lock.get("profile") == "python-app" and "vars" not in lock)
            ok("docs projet intactes hors migration (cadrage, ROADMAP, CHANGELOG)",
               sh(["git", "diff", "--name-only", "--", ".claude/docs"], cwd=p).stdout.split()
               in ([], [".claude/docs/HANDOFF.md"]))

    # ── 2. Personnalisations et conflits ────────────────────────────────────────────────────
    base_tag = "v1.4.1" if "v1.4.1" in TAGS else olds[-1]
    print(f"\n== 2. personnalisations ({base_tag} → {target_v}) ==")
    p = init_project(base_tag, "python-app", TMP / "custom")
    st = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    st["permissions"]["allow"].append("Bash(make:*)")
    st["permissions"]["allow"].remove("Bash(npm:*)")
    st["hooks"].setdefault("PostToolUse", []).append(
        {"matcher": "Write", "hooks": [{"type": "command", "command": "echo maison", "timeout": 3}]})
    (p / ".claude/settings.json").write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gw = p / ".claude/rules/git-workflow.md"
    gw.write_text(gw.read_text(encoding="utf-8").replace(
        "- Pas de SemVer (projet client, pas une lib)\n",
        "- Pas de SemVer (projet client, pas une lib)\n- ✅ Revue par un pair avant tout merge (règle maison)\n"), encoding="utf-8")
    stop = p / ".claude/hooks/stop-handoff-reminder.sh"
    stop.write_text(stop.read_text(encoding="utf-8").replace('"$AGE_HOURS" -lt 24', '"$AGE_HOURS" -lt 48'), encoding="utf-8")
    (p / ".claude/skills/deploy-client").mkdir()
    (p / ".claude/skills/deploy-client/SKILL.md").write_text("---\nname: deploy-client\ndescription: maison\n---\n# x\n", encoding="utf-8")
    shutil.rmtree(p / ".claude/skills/pivot")          # retiré ici, inchangé en amont
    shutil.rmtree(p / ".claude/skills/debug")          # retiré ici, MODIFIÉ en amont → conflit
    tm = p / ".claude/rules/template-maintenance.md"   # réécrite en amont → conflit
    tm.write_text(tm.read_text(encoding="utf-8").replace("## Workflow fin de session (CRITIQUE)",
                                                          "## Workflow fin de session (CRITIQUE — maison)"), encoding="utf-8")
    commit(p, "personnalisations")
    before_tm = tm.read_bytes()
    rc, rep = upgrade_json(p)
    acts = {a["path"]: a["action"] for a in rep.get("actions", [])}
    st2 = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    ok("code 1 (conflits à résoudre) et rien d'autre qu'un conflit ne bloque", rc == 1)
    ok("settings : allow-rule maison conservée", "Bash(make:*)" in st2["permissions"]["allow"])
    ok("settings : retrait volontaire respecté (npm pas réintroduit)", "Bash(npm:*)" not in st2["permissions"]["allow"])
    ok("settings : hook maison conservé",
       any(h.get("command") == "echo maison" for g in st2["hooks"].get("PostToolUse", []) for h in g["hooks"]))
    ok("settings : nouveautés amont appliquées (deny .env à toute profondeur, SessionStart resume)",
       "Read(.env.*)" in st2["permissions"]["deny"]
       and any(g.get("matcher") == "startup|resume|clear|compact" for g in st2["hooks"]["SessionStart"]))
    gwt = gw.read_text(encoding="utf-8")
    ok("rule git-workflow : fusion 3 voies propre (ligne maison + correctif gitleaks amont)",
       acts.get(".claude/rules/git-workflow.md") == "merge" and "règle maison" in gwt and ".pre-commit-config.yaml" in gwt)
    stt = stop.read_text(encoding="utf-8")
    ok("hook Stop : seuil maison (48 h) + correctif amont (1×/session) fusionnés",
       '"$AGE_HOURS" -lt 48' in stt and "first_time handoff-age-warned" in stt
       and sh(["bash", "-n", str(stop)], check=False).returncode == 0)
    ok("skill maison intact", (p / ".claude/skills/deploy-client/SKILL.md").is_file())
    ok("skill retiré ici et inchangé en amont → reste retiré", not (p / ".claude/skills/pivot").exists())
    ok("skill retiré ici mais modifié en amont → conflit signalé, pas réintroduit",
       not (p / ".claude/skills/debug").exists() and ".claude/skills/debug/SKILL.md" in rep.get("conflicts", []))
    aside = p / f".claude/.cache/upgrade-{target_v}"
    ok("conflit texte : fichier du projet GARDÉ tel quel", tm.read_bytes() == before_tm
       and ".claude/rules/template-maintenance.md" in rep.get("conflicts", []))
    ok("conflit : version cible déposée à côté + REPORT.md",
       (aside / ".claude/rules/template-maintenance.md.template").is_file() and (aside / "REPORT.md").is_file())
    ok("fichiers non touchés ici → mis à jour (hook SessionEnd)",
       acts.get(".claude/hooks/sessionend-snapshot.py") == "update")

    # ── 3. Projet < 1.4 qui a grossi → migration de la doc, rien de perdu ─────────────────────
    old = "v1.3.3" if "v1.3.3" in TAGS else None
    if old:
        print(f"\n== 3. projet {old} qui a grossi (journal, gotchas, ROADMAP en @) → {target_v} ==")
        p = init_project(old, "python-app", TMP / "grown")
        ho = p / ".claude/docs/HANDOFF.md"
        journal = "".join(f"- 2026-0{1 + i % 8}-{10 + i % 18} — session {i} : avancement sur la feature {i % 7}\n"
                          for i in range(60))
        ho.write_text(ho.read_text(encoding="utf-8") + "\n## Journal\n\n" + journal, encoding="utf-8")
        cm = p / ".claude/docs/code-map.md"
        gotchas = "".join(f"- ⚠️ `src/mod{i}.py` — piège numéro {i} : l'API renvoie 200 même en erreur\n" for i in range(12))
        # 10 gotchas dans la section du gabarit (usage normal) + 2 dans une section empilée en fin
        # de fichier (robustesse : toutes les sections Gotchas doivent sortir)
        g = gotchas.split("\n")
        cmt = cm.read_text(encoding="utf-8").replace("## Gotchas (pièges non évidents)\n",
                                                      "## Gotchas (pièges non évidents)\n\n" + "\n".join(g[:10]) + "\n", 1)
        cm.write_text(cmt + "\n## Gotchas (pièges non évidents)\n\n" + "\n".join(g[10:]), encoding="utf-8")
        (p / ".claude/docs/specs/001-caisse").mkdir(parents=True, exist_ok=True)
        (p / ".claude/docs/specs/001-caisse/spec.md").write_text("# spec 001\ncontenu précieux\n", encoding="utf-8")
        commit(p, "croissance")
        before = json.loads(sh([sys.executable, str(BUDGET), "--root", str(p), "--json", "--no-user"], check=False).stdout)
        rc, rep = upgrade_json(p)
        after = json.loads(sh([sys.executable, str(BUDGET), "--root", str(p), "--json", "--no-user"], check=False).stdout)
        ok("upgrade sans conflit (projet non personnalisé)", rc == 0)
        jr = p / ".claude/docs/HANDOFF-journal.md"
        ok("migration 1.4.0 : les 60 entrées du journal déplacées dans HANDOFF-journal.md (aucune perdue)",
           jr.is_file() and all(f"session {i} :" in jr.read_text(encoding="utf-8") for i in range(60))
           and "session 42 :" not in ho.read_text(encoding="utf-8"))
        gf = p / ".claude/docs/code-map-gotchas.md"
        ok("migration 1.4.0 : les 12 gotchas sortis de code-map.md (auto-chargée) vers code-map-gotchas.md",
           gf.is_file() and all(f"piège numéro {i} " in gf.read_text(encoding="utf-8") for i in range(12))
           and "piège numéro 3 " not in cm.read_text(encoding="utf-8"))
        ok("spec du projet intacte", (p / ".claude/docs/specs/001-caisse/spec.md").read_text(encoding="utf-8")
           == "# spec 001\ncontenu précieux\n")
        ok(f"budget auto-chargé : {before['total_tok']} → {after['total_tok']} tok (baisse, sous 8k)",
           after["total_tok"] < before["total_tok"] and after["total_tok"] < 8000)
        ok("migrations annoncées dans le rapport", any("1.4.0" in m for m in rep.get("migrations", [])))

    # ── 4. Profils déduits ─────────────────────────────────────────────────────────────────
    print("\n== 4. profils déduits ==")
    t_sj = "v1.2.0" if "v1.2.0" in TAGS else olds[-1]
    p = init_project(t_sj, "script-jetable", TMP / "jetable")
    rc, rep = upgrade_json(p)
    ok(f"script-jetable ({t_sj}) déduit, code 0", rc == 0 and rep.get("profile", "").startswith("script-jetable"))
    ok("script-jetable : pas de greffe des skills retirés par le profil (spec, conception, USAGE)",
       not (p / ".claude/skills/spec").exists() and not (p / ".claude/skills/conception").exists()
       and not (p / ".claude/USAGE.md").exists())
    ok("script-jetable : /upgrade-template ajouté (cycle de vie commun à tous les profils)",
       (p / ".claude/skills/upgrade-template/SKILL.md").is_file())
    ok("script-jetable : = init fraîche du profil", method_files(p) == method_files(fresh("script-jetable")))
    p = init_project(base_tag, "web-app", TMP / "web", extra=lambda d: (d / "package.json").write_text("{}\n"))
    rc, rep = upgrade_json(p)
    ok("web-app déduit (package.json sans pyproject) → rules web ajoutées, rules Python retirées",
       rc == 0 and rep.get("profile", "").startswith("web-app")
       and (p / ".claude/rules/code-style-web.md").is_file() and not (p / ".claude/rules/code-style.md").exists())

    # ── 5. dry-run, arbre sale, équipe active ─────────────────────────────────────────────────
    print("\n== 5. dry-run · arbre sale · équipe d'agents active ==")
    p = init_project(base_tag, "python-app", TMP / "dry")
    h0 = tree_hash(p)
    rc, rep = upgrade_json(p, "--dry-run")
    ok("dry-run : plan produit, AUCUN fichier modifié", rc == 0 and rep.get("actions") and tree_hash(p) == h0)
    (p / "notes.txt").write_text("wip\n")
    rc, rep = upgrade_json(p)
    ok("arbre git sale → refus (code 2), rien d'écrit", rc == 2 and tree_hash(p) != h0 and not (p / ".claude/template-lock.json").exists())
    (p / "notes.txt").unlink()
    st = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    st["enabledPlugins"] = {"agent-teams@claude-setup": True}
    (p / ".claude/settings.json").write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
    commit(p, "plugin agent-teams activé")
    rc, rep = upgrade_json(p)
    st2 = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    ok("équipe active : flag + teammateMode conservés, enabledPlugins intact",
       st2.get("env", {}).get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1" and "teammateMode" in st2
       and st2.get("enabledPlugins") == {"agent-teams@claude-setup": True})
    rule = p / ".claude/rules/agent-teams.md"
    ok("équipe active : rule d'équipe mise à jour depuis le plugin (pas retirée)",
       rule.is_file() and rule.read_bytes() == (ROOT / "plugins/agent-teams/skills/team/agent-teams-rule.md").read_bytes())
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{'🎉 UPGRADE OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
