#!/usr/bin/env python3
"""Tests de régression de cleanup-for-type.py (init + adopt).

Bug critique historique (review 2026-07-07) : strip_template_maintenance supprimait
INCONDITIONNELLEMENT .github/, test/, plugins/ — or en flux /adopt-template (brownfield),
ces dossiers appartiennent au PROJET de l'utilisateur (le rsync d'adopt exclut ceux du
template) → CI, tests et code du client détruits, puis commités. Et prune_dead_permissions
effaçait des allow-rules vivantes (globs traités en littéral, chemins ~/.claude matchés
en substring).

Garde-fous testés ici :
  1. sentinelles de propriété — un dossier homonyme SANS sentinelle template n'est pas touché
  2. mode --brownfield — aucun strip, suppressions de profil confinées à .claude/, ni prune
  3. précision de prune_dead_permissions — globs et chemins hors-projet CONSERVÉS
  4. purge des lignes d'inventaire bootstrap dans les index shippés
  5. --dry-run — ne supprime rien

Usage : python3 test/test_cleanup.py   (exit 0 = tout vert)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".claude" / "skills" / "init-from-template" / "scripts" / "cleanup-for-type.py"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def write(p: Path, text="x\n"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(root: Path, *args):
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  --- stdout ---\n" + r.stdout[-1500:])
        print("  --- stderr ---\n" + r.stderr[-1500:])
    return r


ALLOW_RULES = [
    "Bash(python3 .claude/skills/init-from-template/scripts/render.py:*)",  # morte post-strip
    "Bash(chmod +x .claude/hooks/*.py)",                                    # glob → à GARDER
    "Bash(bash ~/.claude/tools/deploy.sh:*)",                               # hors projet → à GARDER
    "Bash(python3 .claude/tools/mytool.py:*)",                              # script existant → à GARDER
    "Bash(git status)",                                                     # sans chemin → à GARDER
]


def scaffold_template_bits(root: Path):
    """Le scaffold que le template pose dans tout projet (bootstrap skills, docs)."""
    write(root / ".claude" / "skills" / "init-from-template" / "scripts" / "cleanup-for-type.py")
    write(root / ".claude" / "skills" / "adopt-template" / "SKILL.md")
    write(root / ".claude" / "skills" / "handoff" / "SKILL.md")
    write(root / ".claude" / "docs" / "RUNBOOK.md")
    write(root / "CLAUDE.md", "# projet\n")
    write(root / ".claude" / "CLAUDE.md",
          "## Bootstrap\n\n- `/init-from-template` — init one-shot\n"
          "- `/adopt-template` — brownfield one-shot\n- `/handoff` — fin de session\n")
    write(root / "USAGE.md",
          "| Nouveau projet | `/init-from-template` |\n| Fin de session | `/handoff` |\n")
    write(root / ".claude" / "rules" / "template-maintenance.md",
          "| `/init-from-template` ⭐ | UNE FOIS |\n| `/handoff` ⭐ | fin de session |\n")
    write(root / ".claude" / "tools" / "mytool.py")
    write(root / ".claude" / "settings.json",
          json.dumps({"permissions": {"allow": list(ALLOW_RULES)}}, indent=2))


def make_greenfield(tmp: Path) -> Path:
    """Projet GREENFIELD copié intégralement (ex. git clone) : artefacts de maintenance
    présents AVEC leurs sentinelles template."""
    root = tmp / "greenfield"
    scaffold_template_bits(root)
    write(root / ".github" / "workflows" / "ci.yml", "run: python3 test/test_hooks.py\n")
    write(root / ".github" / "CHANGELOG.md")
    write(root / "test" / "test_hooks.py")
    write(root / "EXAMPLES" / "acme-sync-erp-notion-docs" / "_CLAUDE.md")
    write(root / "plugins" / "n8n-expertise" / ".claude-plugin" / "plugin.json", "{}\n")
    write(root / ".claude-plugin" / "marketplace.json", "{}\n")
    write(root / "workflows" / "README.md")
    return root


def make_brownfield(tmp: Path) -> Path:
    """Projet EXISTANT adopté : .github/test/plugins/EXAMPLES/workflows appartiennent à
    l'USER (pas de sentinelle template), le scaffold .claude/ vient d'être rsyncé."""
    root = tmp / "brownfield"
    scaffold_template_bits(root)
    write(root / ".github" / "workflows" / "deploy-user.yml", "on: push\n")
    write(root / "test" / "test_user_app.py")
    write(root / "plugins" / "ma-lib-maison" / "util.py")
    write(root / "EXAMPLES" / "doc-interne.md")
    write(root / "workflows" / "export-perso.json")
    return root


def allow_of(root: Path):
    return json.loads((root / ".claude" / "settings.json").read_text())["permissions"]["allow"]


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)

    print("\n== 1. GREENFIELD : strip complet (sentinelles présentes) + prune précis ==")
    g = make_greenfield(tmp)
    r = run(g, "--type", "python-app")
    ok("exit 0", r.returncode == 0)
    for gone in (".github", "test", "EXAMPLES", "plugins", ".claude-plugin",
                 ".claude/skills/init-from-template", ".claude/skills/adopt-template",
                 "workflows", ".claude/docs/RUNBOOK.md"):
        ok(f"supprimé : {gone}", not (g / gone).exists())
    ok("conservé : .claude/skills/handoff", (g / ".claude/skills/handoff/SKILL.md").exists())
    allow = allow_of(g)
    ok("prune : règle render.py morte retirée", ALLOW_RULES[0] not in allow)
    ok("prune : règle GLOB conservée", ALLOW_RULES[1] in allow)
    ok("prune : règle ~/.claude conservée", ALLOW_RULES[2] in allow)
    ok("prune : règle script existant conservée", ALLOW_RULES[3] in allow)
    ok("prune : règle sans chemin conservée", ALLOW_RULES[4] in allow)
    inv = (g / ".claude" / "CLAUDE.md").read_text()
    ok("inventaire : bullets bootstrap purgés", "/init-from-template" not in inv and "/adopt-template" not in inv)
    ok("inventaire : bullet /handoff conservé", "/handoff" in inv)
    ok("inventaire USAGE : ligne bootstrap purgée", "/init-from-template" not in (g / "USAGE.md").read_text())
    ok("inventaire rules : ligne bootstrap purgée",
       "/init-from-template" not in (g / ".claude/rules/template-maintenance.md").read_text())

    print("\n== 2. HOMONYMES : dossiers user SANS sentinelle → jamais touchés (même sans flag) ==")
    h = tmp / "homonymes"
    scaffold_template_bits(h)
    write(h / ".github" / "workflows" / "deploy.yml", "on: push\n")   # pas la CI du template
    write(h / "test" / "test_app.py")                                  # pas test_hooks.py
    write(h / "plugins" / "monlib" / "util.py")                        # pas de marketplace.json
    write(h / "EXAMPLES" / "notes.md")                                 # pas d'acme
    r = run(h, "--type", "python-app")
    ok("exit 0", r.returncode == 0)
    ok("conservé : .github/ user", (h / ".github/workflows/deploy.yml").exists())
    ok("conservé : test/ user", (h / "test/test_app.py").exists())
    ok("conservé : plugins/ user", (h / "plugins/monlib/util.py").exists())
    ok("conservé : EXAMPLES/ user", (h / "EXAMPLES/notes.md").exists())
    ok("bootstrap quand même retiré (nom spécifique template)",
       not (h / ".claude/skills/init-from-template").exists())

    print("\n== 3. BROWNFIELD (--brownfield) : rien de l'user touché, ni strip ni prune ==")
    b = make_brownfield(tmp)
    r = run(b, "--type", "python-app", "--brownfield")
    ok("exit 0", r.returncode == 0)
    ok("conservé : .github/ user", (b / ".github/workflows/deploy-user.yml").exists())
    ok("conservé : test/ user", (b / "test/test_user_app.py").exists())
    ok("conservé : plugins/ user", (b / "plugins/ma-lib-maison/util.py").exists())
    ok("conservé : EXAMPLES/ user", (b / "EXAMPLES/doc-interne.md").exists())
    ok("conservé : workflows/ user (delete profil hors .claude/ ignoré)",
       (b / "workflows/export-perso.json").exists())
    ok("conservé : skills bootstrap (retrait manuel Étape 5)",
       (b / ".claude/skills/init-from-template").exists() and (b / ".claude/skills/adopt-template").exists())
    ok("appliqué : delete profil SOUS .claude/ (RUNBOOK)", not (b / ".claude/docs/RUNBOOK.md").exists())
    ok("permissions INTACTES (prune sauté)", allow_of(b) == ALLOW_RULES)
    ok("inventaires INTACTS", "/init-from-template" in (b / ".claude" / "CLAUDE.md").read_text())

    print("\n== 4. DRY-RUN : ne supprime rien ==")
    d = make_greenfield(tmp)
    r = run(d, "--type", "automation-n8n", "--dry-run")
    ok("exit 0", r.returncode == 0)
    ok("rien supprimé (.github toujours là)", (d / ".github/workflows/ci.yml").exists())
    ok("rien supprimé (plugins toujours là)", (d / "plugins").exists())
    ok("settings intact", allow_of(d) == ALLOW_RULES)

print(f"\n{'🎉 CLEANUP OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
