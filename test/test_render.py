#!/usr/bin/env python3
"""Tests de régression de render.py (init-from-template).

Bug historique (découvert au 1er init réel, 2026-07-05, projet projetA) : les
motifs EXCLUDE étaient testés en substring sur le chemin ABSOLU — un projet
situé sous un dossier parent nommé comme un motif (ex. /mnt/e/.../test/projetA)
voyait TOUS ses fichiers exclus → « 0 fichiers à scanner » → init
silencieusement à vide, sans erreur.

Usage : python3 test/test_render.py   (exit 0 = tout vert)
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / ".claude" / "skills" / "init-from-template" / "scripts" / "render.py"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def run_render(*args):
    return subprocess.run([sys.executable, str(RENDER), *args],
                          capture_output=True, text=True)


# Sandbox : le projet vit VOLONTAIREMENT sous un parent nommé "test/" (repro du bug)
base = Path(tempfile.mkdtemp(prefix="rendertest-"))
proj = base / "test" / "projetX"
(proj / "latest").mkdir(parents=True)          # piège substring : "latest/" contient "test"
(proj / "EXAMPLES").mkdir()
(proj / ".claude" / "skills" / "foo").mkdir(parents=True)
(proj / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\nClient : {{CLIENT_NAME}}\n")
(proj / "latest" / "notes.md").write_text("{{PROJECT_NAME}} encore\n")
(proj / "EXAMPLES" / "skip.md").write_text("{{PROJECT_NAME}} exemple à NE PAS toucher\n")
(proj / ".claude" / "skills" / "foo" / "SKILL.md").write_text("{{PROJECT_NAME}} doc skill à NE PAS toucher\n")

print("== find_files : exclusions relatives, ancrées sur segments ==")
r = run_render("--root", str(proj), "--list-placeholders", "--core")
ok("projet sous parent test/ → fichiers trouvés (régression bug)", "0 fichiers à scanner" not in r.stdout)
ok("CORE PROJECT_NAME détecté", "PROJECT_NAME" in r.stdout)
ok("CORE CLIENT_NAME détecté", "CLIENT_NAME" in r.stdout)

print("\n== substitution --vars ==")
vars_file = base / "vars.json"
vars_file.write_text(json.dumps({"PROJECT_NAME": "projetX", "CLIENT_NAME": "ACME"}))
r2 = run_render("--root", str(proj), "--vars", str(vars_file))
ok("substitution exécutée (exit 0)", r2.returncode == 0)
ok("CLAUDE.md substitué", "projetX" in (proj / "CLAUDE.md").read_text())
ok("latest/ PAS exclu par le motif test/ (ancrage segments)",
   "projetX" in (proj / "latest" / "notes.md").read_text())
ok("EXAMPLES/ toujours exclu", "{{PROJECT_NAME}}" in (proj / "EXAMPLES" / "skip.md").read_text())
ok(".claude/skills/ toujours exclu",
   "{{PROJECT_NAME}}" in (proj / ".claude" / "skills" / "foo" / "SKILL.md").read_text())

print("\n== --check ==")
r3 = run_render("--root", str(proj), "--check")
ok("--check vert après substitution (exit 0)",
   r3.returncode == 0 and "Tous les placeholders CORE" in r3.stdout)
(proj / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\n")  # re-casse un CORE
r4 = run_render("--root", str(proj), "--check")
ok("--check rouge si CORE restant (exit 1)", r4.returncode == 1)

shutil.rmtree(base, ignore_errors=True)
print(f"\n{'🎉 RENDER OK' if FAIL == 0 else '⚠️  ÉCHEC'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
