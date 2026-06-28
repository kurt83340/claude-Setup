#!/usr/bin/env python3
"""Suite de tests des 5 hooks du template (régression).

Pourquoi : les hooks tournent à CHAQUE action Claude — un hook cassé dégrade en
silence chaque session. Cette suite s'exécute sans dépendance externe (stdlib).

Usage : python3 test/test_hooks.py     (exit 0 = tout vert)
"""
import json, os, py_compile, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
DOCS = ROOT / ".claude" / "docs"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def run_hook(name, payload, cwd):
    exe = ["bash", str(HOOKS / name)] if name.endswith(".sh") else [sys.executable, str(HOOKS / name)]
    return subprocess.run(exe, input=json.dumps(payload), capture_output=True, text=True, cwd=cwd)


def sandbox():
    sb = Path(tempfile.mkdtemp(prefix="hooktest-"))
    (sb / ".claude" / "docs").mkdir(parents=True)
    return sb


# 0. Compilation
print("== compilation ==")
for h in HOOKS.glob("*.py"):
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

# 3. pretooluse-inject-codemap → injecte sur code, pas sur .md
print("\n== pretooluse-inject-codemap ==")
sb = sandbox()
if (DOCS / "code-map.md").exists():
    shutil.copy2(DOCS / "code-map.md", sb / ".claude/docs/code-map.md")
    r = run_hook("pretooluse-inject-codemap.py",
                 {"tool_name": "Edit", "tool_input": {"file_path": str(sb / "src/app.py")}, "cwd": str(sb)}, sb)
    try:
        inj = json.loads(r.stdout).get("hookSpecificOutput", {}).get("additionalContext", "")
    except Exception:
        inj = ""
    ok("contexte injecté pour fichier src/", "Règles de couplage" in inj)
    r2 = run_hook("pretooluse-inject-codemap.py",
                  {"tool_name": "Edit", "tool_input": {"file_path": str(sb / "src/README.md")}, "cwd": str(sb)}, sb)
    ok("pas d'injection pour un .md", r2.stdout.strip() == "")
else:
    ok("code-map.md absent du template (skip)", True)
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
    r2 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb)}, sb)
    ok("HANDOFF vieux + git dirty → rappel", "HANDOFF" in r2.stdout)
    # gate lead-only : un teammate identifié (agent_type≠lead) ne rappelle PAS
    r3 = run_hook("stop-handoff-reminder.sh", {"cwd": str(sb), "agent_type": "Explore"}, sb)
    ok("teammate (agent_type≠lead) → pas de rappel", r3.stdout.strip() == "")
    # levier env : CLAUDE_HANDOFF_REMINDER=off coupe le rappel (cas sessions teammate top-level)
    r4 = subprocess.run(["bash", str(HOOKS / "stop-handoff-reminder.sh")],
                        input=json.dumps({"cwd": str(sb)}), capture_output=True, text=True,
                        cwd=sb, env=dict(os.environ, CLAUDE_HANDOFF_REMINDER="off"))
    ok("CLAUDE_HANDOFF_REMINDER=off → pas de rappel", r4.stdout.strip() == "")
else:
    ok("git absent (skip test rappel)", True)
shutil.rmtree(sb, ignore_errors=True)

print(f"\n{'🎉 TOUS LES HOOKS OK' if FAIL == 0 else '⚠️  ÉCHEC'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
