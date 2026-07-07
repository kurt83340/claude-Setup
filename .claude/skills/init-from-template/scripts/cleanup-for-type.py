#!/usr/bin/env python3
"""
cleanup-for-type.py — Adapte le template selon le type de projet.

Le template par défaut est dimensionné pour un projet "moyen" (automation n8n,
python app, web app). Pour un script jetable c'est trop ; pour une web app
enterprise c'est insuffisant. Ce script ajuste.

Types supportés :
  - script-jetable : -80% (garde minimum vital pour 1-shot)
  - automation-n8n : ajustement léger (retire RUNBOOK pas-encore-prod)
  - python-app    : retire workflows/, garde tout sinon
  - web-app       : retire workflows/ (pas n8n)
  - bdd-migration : retire workflows/ (skill db-migration = plugin à installer)

Usage:
    python3 cleanup-for-type.py --type script-jetable [--root .] [--dry-run]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# ============================================================================
# Définition des actions par type
# ============================================================================

# script-jetable : 1-shot, < 1 jour, pas de feature multiple, pas de prod
SCRIPT_JETABLE = {
    "delete": [
        # Doc conception entière (overkill pour 1-shot)
        ".claude/docs/conception/",
        # Transversaux pas pertinents
        ".claude/docs/adr/",
        ".claude/docs/idees/",
        ".claude/docs/ROADMAP.md",
        ".claude/docs/RUNBOOK.md",
        ".claude/docs/code-map.md",
        ".claude/docs/stack.md",
        ".claude/docs/ACCESS.md",
        ".claude/docs/GLOSSARY.md",
        # NB: lecons.md est CONSERVÉ — /lecon fait partie du trio vital (handoff, lecon,
        # init) ; supprimer son fichier cible rendrait /lecon capture orphelin. Sur un
        # jetable, /lecon promote→ADR n'est pas dispo (pas de /adr), mais capture/discard si.
        # Cadrage sous-dossiers (le README suffit)
        ".claude/docs/cadrage/tickets/",
        ".claude/docs/cadrage/reunions/",
        ".claude/docs/cadrage/documents/",
        ".claude/docs/cadrage/diagrams/",
        # Skills overkill (script-jetable garde uniquement handoff, lecon, init)
        ".claude/skills/adr/",
        ".claude/skills/codemap/",
        ".claude/skills/doc-health/",
        ".claude/skills/feature-done/",
        ".claude/skills/spec/",
        ".claude/skills/pivot/",
        ".claude/skills/idee/",
        ".claude/skills/team/",
        ".claude/skills/conception/",
        ".claude/skills/debug/",
        ".claude/skills/adopt-template/",
        # Agents (pas besoin doc-maintainer pour 1-shot)
        ".claude/agents/",
        # Hooks code (pas de code structuré)
        ".claude/hooks/pretooluse-inject-codemap.py",
        ".claude/hooks/posttooluse-growth-detection.py",
        # Workflows folder
        "workflows/",
    ],
    "keep_reason": "1-shot script — minimum vital : cadrage, HANDOFF, CHANGELOG, /handoff, /lecon",
}

# automation-n8n : ajustement léger (les skills n8n sont un PLUGIN, plus de copie)
AUTOMATION_N8N = {
    "delete": [
        # RUNBOOK créé post-prod uniquement
        ".claude/docs/RUNBOOK.md",
    ],
    "keep_reason": "n8n full stack — retire RUNBOOK (créé post-prod). Skills n8n = plugin 'n8n-expertise' à installer (/plugin install n8n-expertise@claude-setup), plus de copie.",
}

# python-app : retire workflows/
PYTHON_APP = {
    "delete": [
        "workflows/",
        ".claude/docs/RUNBOOK.md",
    ],
    "keep_reason": "Python app — retire workflows/ (pas n8n)",
}

# web-app : retire workflows/
WEB_APP = {
    "delete": [
        "workflows/",
        ".claude/docs/RUNBOOK.md",
    ],
    "keep_reason": "Web app — retire workflows/ (pas n8n)",
}

# bdd-migration : retire workflows/ (le skill db-migration est un PLUGIN, plus de copie)
BDD_MIGRATION = {
    "delete": [
        "workflows/",
    ],
    "keep_reason": "BDD migration — retire workflows/. Skill db-migration (Alembic) = plugin à installer (/plugin install db-migration@claude-setup), plus de copie.",
}

PROFILES = {
    "script-jetable": SCRIPT_JETABLE,
    "automation-n8n": AUTOMATION_N8N,
    "python-app": PYTHON_APP,
    "web-app": WEB_APP,
    "bdd-migration": BDD_MIGRATION,
}

# ── Artefacts de maintenance DU TEMPLATE (retirés pour TOUS les types) ─────────
# N'existent que pour développer/distribuer le template lui-même. Un projet GÉNÉRÉ n'en a
# aucun usage — et la self-CI (.github/workflows/ci.yml) teste render.py / l'inventaire, que
# l'init vient justement de supprimer → CI ROUGE héritée. Les plugins stack (plugins/ +
# .claude-plugin/) sont la SOURCE du marketplace : le projet les INSTALLE (/plugin), il ne les
# embarque pas. init-from-template/ est retiré EN DERNIER : il contient CE script (suppression
# OK sous POSIX — le process tourne en mémoire). Réversible : le snapshot git pre-init garde tout.
TEMPLATE_MAINTENANCE = [
    ".github/",                            # self-CI + README/CHANGELOG DU template
    "test/",                               # tests + rapports d'audit DU template
    "EXAMPLES/",                           # exemple rempli (acme) — référence, pas du projet
    "plugins/",                            # SOURCE des plugins stack → le projet les installe (marketplace)
    ".claude-plugin/",                     # manifeste marketplace → vit dans le repo template
    ".claude/skills/adopt-template/",      # bootstrap brownfield one-shot (exclusif avec init)
    ".claude/skills/init-from-template/",  # bootstrap one-shot — EN DERNIER (contient ce script)
]


def cleanup(root: Path, profile_name: str, dry_run: bool) -> int:
    if profile_name not in PROFILES:
        print(f"❌ Type inconnu : {profile_name}", file=sys.stderr)
        print(f"   Types valides : {', '.join(PROFILES.keys())}", file=sys.stderr)
        return 1

    profile = PROFILES[profile_name]
    print(f"📋 Profil : {profile_name}")
    print(f"   {profile['keep_reason']}\n")

    deleted_files = 0
    deleted_dirs = 0
    skipped = 0

    for rel_path in profile["delete"]:
        target = root / rel_path
        if not target.exists():
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY] Would delete : {rel_path}")
            if target.is_dir():
                deleted_dirs += 1
            else:
                deleted_files += 1
        else:
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                    deleted_dirs += 1
                    print(f"  🗑️  Deleted dir  : {rel_path}")
                else:
                    target.unlink()
                    deleted_files += 1
                    print(f"  🗑️  Deleted file : {rel_path}")
            except Exception as e:
                print(f"  ⚠️  Échec sur {rel_path} : {e}", file=sys.stderr)

    prefix = "[DRY] " if dry_run else ""
    print(f"\n🎉 {prefix}Cleanup : {deleted_files} fichiers + {deleted_dirs} dossiers supprimés "
          f"({skipped} déjà absents)")

    # Retrait des artefacts de maintenance DU template (tous types)
    strip_template_maintenance(root, dry_run)

    # Post-cleanup : réparer CLAUDE.md + purger settings.json (hooks fantômes + allow-rules mortes)
    if not dry_run:
        fix_claude_md_imports(root)
        prune_dead_hooks(root)
        prune_dead_permissions(root)

    return 0


def strip_template_maintenance(root: Path, dry_run: bool) -> int:
    """Retire les artefacts qui ne servent qu'à maintenir LE TEMPLATE (self-CI, tests, exemples,
    skills bootstrap — voir TEMPLATE_MAINTENANCE). Appelé pour TOUS les types, APRÈS la copie des
    skills stack. Réversible via le snapshot git pre-init."""
    print("\n🧹 Artefacts de maintenance du template (inutiles dans un projet généré) :")
    removed = 0
    for rel in TEMPLATE_MAINTENANCE:
        target = root / rel
        if not target.exists():
            continue
        if dry_run:
            print(f"  [DRY] Would delete : {rel}")
            removed += 1
            continue
        try:
            shutil.rmtree(target) if target.is_dir() else target.unlink()
            print(f"  🗑️  Deleted : {rel}")
            removed += 1
        except Exception as e:
            print(f"  ⚠️  Échec sur {rel} : {e}", file=sys.stderr)
    if removed == 0:
        print("  (rien à retirer — déjà propre)")
    return removed


def prune_dead_permissions(root: Path) -> None:
    """Retire de settings.json les allow-rules Bash pointant vers un script `.claude/…(.py|.sh)`
    désormais absent — ex. les 2 règles init-from-template (render.py / cleanup-for-type.py),
    mortes une fois le skill bootstrap retiré. Générique : matche le chemin, teste l'existence."""
    settings_path = root / ".claude" / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return
    perms = settings.get("permissions")
    if not isinstance(perms, dict) or not isinstance(perms.get("allow"), list):
        return
    script_re = re.compile(r"\.claude/[^\s:\"']+\.(?:py|sh)")
    kept, removed = [], 0
    for rule in perms["allow"]:
        m = script_re.search(rule) if isinstance(rule, str) else None
        if m and not (root / m.group(0)).exists():
            removed += 1
            continue
        kept.append(rule)
    if removed:
        perms["allow"] = kept
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        print(f"🔧 settings.json : {removed} allow-rule(s) morte(s) retirée(s) (script absent)")


def fix_claude_md_imports(root: Path) -> None:
    """Retire les lignes de CLAUDE.md qui pointent vers des fichiers maintenant inexistants."""
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return

    text = claude_md.read_text(encoding="utf-8")
    lines = text.split("\n")
    new_lines = []
    removed = 0

    # Pattern : `@.claude/...` (avec ou sans backticks, dans une ligne)
    import_pattern = re.compile(r"@(\.claude/[^\s\)\]]+)")

    for line in lines:
        matches = import_pattern.findall(line)
        if not matches:
            new_lines.append(line)
            continue

        # Vérifier que tous les @-imports de la ligne existent
        all_exist = all((root / m.rstrip("/")).exists() for m in matches)
        if all_exist:
            new_lines.append(line)
        else:
            removed += 1
            # Skip cette ligne (refs cassées)

    if removed > 0:
        claude_md.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"\n🔧 CLAUDE.md : {removed} lignes avec @-imports cassés retirées")


def prune_dead_hooks(root: Path) -> None:
    """Retire de settings.json les hooks dont le script a été supprimé (sinon hooks fantômes
    → Claude tente d'exécuter un script manquant à chaque event). Générique : s'applique à
    tout profil qui supprime des fichiers .claude/hooks/*."""
    settings_path = root / ".claude" / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return
    script_re = re.compile(r"\.claude/hooks/[^\s\"']+")
    removed = 0
    for event in list(hooks.keys()):
        kept_groups = []
        for group in hooks.get(event, []):
            kept = []
            for h in group.get("hooks", []):
                m = script_re.search(h.get("command", ""))
                if m and not (root / m.group(0)).exists():
                    removed += 1
                    continue  # script supprimé → on retire le hook
                kept.append(h)
            if kept:
                group["hooks"] = kept
                kept_groups.append(group)
        if kept_groups:
            hooks[event] = kept_groups
        else:
            del hooks[event]
    if removed:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        print(f"🔧 settings.json : {removed} hook(s) fantôme(s) retiré(s) (script supprimé)")


def main():
    parser = argparse.ArgumentParser(description="Adapte le template selon le type de projet")
    parser.add_argument("--type", required=True, choices=list(PROFILES.keys()),
                        help="Type de projet")
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="Racine du projet (default: cwd)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Ne pas supprimer, juste lister")
    args = parser.parse_args()

    return cleanup(args.root.resolve(), args.type, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
