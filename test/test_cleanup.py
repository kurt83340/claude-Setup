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
  6. cohérence post-profil (E2E Phase 0 × 5 types, 2026-07-08) — script-jetable : inventaire
     purgé des skills supprimés (forme `/nom` backtickée UNIQUEMENT, jamais les chemins),
     compte « N skills cœur » recalé, sections mortes repliées (Agent perso, Pipelines,
     Agent teams), liens de nav morts recousus, pointeurs create-on-demand CONSERVÉS

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


NAV_CLAUDE_MD = """# projet

### 🔄 Auto-chargés

- Reprise session : @.claude/docs/HANDOFF.md ⭐
- Roadmap : @.claude/docs/ROADMAP.md

### 📂 Lus à la demande

- 🎨 **Conception** : [PRD](.claude/docs/conception/PRD.md) · [tasks](.claude/docs/conception/tasks.md)
- 🔄 **Suivi** : [ACCESS](.claude/docs/ACCESS.md) · [CHANGELOG](.claude/docs/CHANGELOG.md) · [stack](.claude/docs/stack.md)
- 📚 **Transversaux** : [ADR](.claude/docs/adr/) · [GLOSSARY](.claude/docs/GLOSSARY.md)

## Reminders

- Décision structurante → ADR (via `/adr`)
- Fin de session : `/handoff`
"""

INDEX_CLAUDE_MD = """# tpl — skills & agents

## Skills

### Session & feature

- `/handoff` ⭐ — snapshot fin de session
- `/spec "<titre>"` ⭐ — scaffold feature

### Cycle de vie

- `/adr [mode] <args>` — ADRs
- `/lecon [mode] <args>` — leçons

### Bootstrap

- `/init-from-template` — init one-shot
- `/adopt-template` — brownfield one-shot

> 🗂️ **Inventaire canonique** : cette liste (**6 skills cœur**) est la source de vérité.

## 🔁 Pipelines récurrents (orchestrés par `/feature`)

- **standard** : `/spec` → coder → tests

## Agent perso (`.claude/agents/`)

- `doc-maintainer` — subagent doc

## Marketplace

> plugins stack via `/plugin install db-migration@claude-setup`.
"""

MAINTENANCE_MD = """| `/init-from-template` ⭐ | UNE FOIS |
| `/handoff` ⭐ | fin de session |
| `/spec` ⭐ | démarrer une feature |

Détails complets : [adr/README.md](../docs/adr/README.md)

### Agent perso (`.claude/agents/`)

| doc-maintainer | Task tool |

### Agents disponibles

→ [table](../agents/README.md)

## Agent teams — anti-collision

> Source unique : [agent-teams.md](agent-teams.md)

## Fin

ok
"""

CADRAGE_MD = """# Cadrage

**Docs reçus :** voir [documents/](documents/)
**Diagrammes** : [diagrams/README.md](diagrams/README.md)
**Tickets liés :** {{[TICKET-XXX](tickets/TICKET-XXX-...md)}}
"""


def scaffold_template_bits(root: Path):
    """Le scaffold que le template pose dans tout projet (bootstrap skills, docs, nav)."""
    write(root / ".claude" / "skills" / "init-from-template" / "scripts" / "cleanup-for-type.py")
    write(root / ".claude" / "skills" / "adopt-template" / "SKILL.md")
    write(root / ".claude" / "skills" / "handoff" / "SKILL.md")
    write(root / ".claude" / "skills" / "spec" / "SKILL.md")
    write(root / ".claude" / "skills" / "lecon" / "SKILL.md")
    write(root / ".claude" / "skills" / "feature" / "SKILL.md")
    write(root / ".claude" / "agents" / "doc-maintainer.md")
    write(root / ".claude" / "rules" / "agent-teams.md")
    write(root / ".claude" / "docs" / "RUNBOOK.md")
    write(root / ".claude" / "docs" / "HANDOFF.md")
    write(root / ".claude" / "docs" / "ROADMAP.md")
    write(root / ".claude" / "docs" / "stack.md")
    write(root / ".claude" / "docs" / "CHANGELOG.md")
    write(root / ".claude" / "docs" / "lecons.md")
    write(root / ".claude" / "docs" / "conception" / "PRD.md")
    write(root / ".claude" / "docs" / "conception" / "tasks.md")
    write(root / ".claude" / "docs" / "adr" / "README.md")
    write(root / ".claude" / "docs" / "cadrage" / "README.md", CADRAGE_MD)
    write(root / ".claude" / "docs" / "cadrage" / "documents" / "src.md")
    write(root / ".claude" / "docs" / "cadrage" / "diagrams" / "README.md")
    write(root / "CLAUDE.md", NAV_CLAUDE_MD)
    write(root / ".claude" / "CLAUDE.md", INDEX_CLAUDE_MD)
    write(root / ".claude" / "USAGE.md",
          "| Nouveau projet | `/init-from-template` |\n| Fin de session | `/handoff` |\n"
          "| Feature | `/spec` |\n")
    write(root / ".claude" / "STRUCTURE.md", "# Convention\nnpx-free.\n")
    write(root / ".claude" / "rules" / "template-maintenance.md", MAINTENANCE_MD)
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
    write(root / "plugins" / "db-migration" / ".claude-plugin" / "plugin.json", "{}\n")
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
    ok("inventaire : /spec conservé (profil sans skills supprimés)", "`/spec" in inv)
    ok("inventaire : compte « skills cœur » recalé (6→4)", "**4 skills cœur**" in inv)
    ok("inventaire : sections Pipelines + Agent perso conservées",
       "Pipelines récurrents" in inv and "Agent perso" in inv)
    ok("inventaire USAGE : ligne bootstrap purgée", "/init-from-template" not in (g / ".claude/USAGE.md").read_text())
    ok("python-app : USAGE/STRUCTURE (doc méthode) CONSERVÉS dans .claude/",
       (g / ".claude/USAGE.md").exists() and (g / ".claude/STRUCTURE.md").exists())
    tm = (g / ".claude/rules/template-maintenance.md").read_text()
    ok("inventaire rules : ligne bootstrap purgée", "/init-from-template" not in tm)
    ok("rules : sections agents/teams + lien adr conservés",
       "Agent teams" in tm and "Agents disponibles" in tm and "adr/README.md" in tm)
    nav = (g / "CLAUDE.md").read_text()
    ok("nav intacte : @-imports + liens vivants + pointeurs on-demand conservés",
       "@.claude/docs/ROADMAP.md" in nav and "[tasks]" in nav
       and "[ACCESS]" in nav and "[GLOSSARY]" in nav)

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
    ok("inventaire/nav non modifiés en dry-run",
       "**6 skills cœur**" in (d / ".claude/CLAUDE.md").read_text())
    ok("message n8n → plugin OFFICIEL n8n-mcp-skills (plus n8n-expertise)",
       "n8n-mcp-skills" in r.stdout and "n8n-expertise" not in r.stdout)

    print("\n== 5. SCRIPT-JETABLE : cohérence post-profil (inventaire, sections, nav) ==")
    j = make_greenfield(tmp)
    r = run(j, "--type", "script-jetable")
    ok("exit 0", r.returncode == 0)
    ok("rule agent-teams supprimée (protocole équipe sans objet en 1-shot)",
       not (j / ".claude/rules/agent-teams.md").exists())
    ok("vitaux conservés : lecons.md + CHANGELOG + skills handoff/lecon",
       (j / ".claude/docs/lecons.md").exists() and (j / ".claude/docs/CHANGELOG.md").exists()
       and (j / ".claude/skills/handoff/SKILL.md").exists()
       and (j / ".claude/skills/lecon/SKILL.md").exists())
    inv = (j / ".claude" / "CLAUDE.md").read_text()
    ok("inventaire : skills du profil purgés (`/spec`, `/adr`)",
       "`/spec" not in inv and "`/adr" not in inv)
    ok("inventaire : vitaux conservés (`/handoff`, `/lecon`)",
       "`/handoff" in inv and "`/lecon" in inv)
    ok("inventaire : compte recalé (6→2 skills cœur)", "**2 skills cœur**" in inv)
    ok("inventaire : sections mortes repliées (Agent perso, Pipelines)",
       "Agent perso" not in inv and "Pipelines récurrents" not in inv)
    ok("inventaire : section suivante intacte (Marketplace)", "## Marketplace" in inv)
    nav = (j / "CLAUDE.md").read_text()
    ok("nav : @-import HANDOFF conservé, ROADMAP mort retiré",
       "@.claude/docs/HANDOFF.md" in nav and "ROADMAP" not in nav)
    ok("nav : ligne Conception (100% morte) retirée", "Conception" not in nav)
    ok("nav : lien stack mort retiré, CHANGELOG recousu",
       "[stack]" not in nav and "[CHANGELOG](.claude/docs/CHANGELOG.md)" in nav)
    ok("nav : pointeurs create-on-demand CONSERVÉS (ACCESS, GLOSSARY)",
       "[ACCESS]" in nav and "[GLOSSARY]" in nav)
    ok("nav : segment ADR mort retiré (chemin ≠ réf skill)", "(.claude/docs/adr/)" not in nav)
    ok("nav : recousue sans séparateur orphelin",
       "·  ·" not in nav and ": ·" not in nav
       and not any(l.rstrip().endswith("·") for l in nav.split("\n")))
    ok("nav : reminder `/adr` purgé, `/handoff` conservé",
       "(via `/adr`)" not in nav and "`/handoff`" in nav)
    cad = (j / ".claude/docs/cadrage/README.md").read_text()
    ok("cadrage : liens vers sous-dossiers supprimés purgés",
       "[documents/]" not in cad and "diagrams/README.md" not in cad)
    ok("cadrage : ligne pattern (TICKET-XXX) conservée", "TICKET-XXX" in cad)
    tm = (j / ".claude/rules/template-maintenance.md").read_text()
    ok("rules : rangée `/spec` purgée, `/handoff` conservée",
       "`/spec" not in tm and "`/handoff" in tm)
    ok("rules : sections agents/teams repliées",
       "Agent perso" not in tm and "Agents disponibles" not in tm and "Agent teams" not in tm)
    ok("rules : lien adr mort purgé, section suivante intacte",
       "adr/README.md" not in tm and "## Fin" in tm)

    print("\n== 6. Blocs anti-mauvais-routage (v0.19) : purge des segments morts chez les survivants ==")
    j6 = make_greenfield(tmp)
    write(j6 / ".claude/skills/handoff/SKILL.md",
          "# /handoff — Snapshot fin de session\n\n"
          "> **Quand ne PAS utiliser** : reprendre une session précise → `/resume` (natif) ·\n"
          "> feature terminée à livrer → `/feature-done` · pattern appris → `/lecon`.\n"
          "> **Réversibilité** : 🟢 n'écrit que HANDOFF — undo : `git checkout`.\n\n"
          "Ton rôle : snapshot.\n")
    write(j6 / ".claude/skills/lecon/SKILL.md",
          "# /lecon — Cycle de vie des leçons\n\n"
          "> **Quand ne PAS utiliser** : décision structurante → `/adr` · idée produit → `/idee`.\n"
          "> **Réversibilité** : 🟢 append une entry — undo : sous-mode discard.\n\n"
          "Ton rôle : leçons.\n")
    write(j6 / "vars.json", '{"PROJECT_NAME": "x", "TON_EMAIL": "a@b.c"}')
    r = run(j6, "--type", "script-jetable")
    ok("exit 0", r.returncode == 0)
    ok("filet vars.json : matériau d'init (PII) supprimé", not (j6 / "vars.json").exists())
    ok("script-jetable : USAGE/STRUCTURE (1 600 lignes de méthode) STRIPPÉS",
       not (j6 / ".claude/USAGE.md").exists() and not (j6 / ".claude/STRUCTURE.md").exists())
    ho6 = (j6 / ".claude/skills/handoff/SKILL.md").read_text()
    ok("handoff : segment `/feature-done` (skill strippé) purgé", "/feature-done" not in ho6)
    ok("handoff : `/resume` (builtin) + `/lecon` (survivant) conservés",
       "`/resume`" in ho6 and "`/lecon`" in ho6)
    ok("handoff : recousu proprement (pas de séparateur orphelin, point final)",
       "· ·" not in ho6 and "· ." not in ho6 and "`/lecon`." in ho6)
    lc6 = (j6 / ".claude/skills/lecon/SKILL.md").read_text()
    ok("lecon : ligne « Quand ne PAS utiliser » 100 % morte retirée entière",
       "Quand ne PAS utiliser" not in lc6)
    ok("lecon : ligne « Réversibilité » conservée", "**Réversibilité**" in lc6)

print(f"\n{'🎉 CLEANUP OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
