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
  - bdd-migration : copie le skill db-migration depuis EXAMPLES/skills-db

Usage:
    python3 cleanup-for-type.py --type script-jetable [--root .] [--dry-run]
"""

import argparse
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

# automation-n8n : ajustement léger + copie skills n8n depuis EXAMPLES
AUTOMATION_N8N = {
    "delete": [
        # RUNBOOK créé post-prod uniquement
        ".claude/docs/RUNBOOK.md",
    ],
    "copy_examples": {
        # Source EXAMPLES → destination .claude/
        # Note: skills à plat dans .claude/skills/ (1 niveau, cf. issue #18192) ;
        # mapping par skill car copy_from_examples skip si la destination existe
        # (.claude/skills/ existe toujours).
        "EXAMPLES/skills-n8n/n8n-push": ".claude/skills/n8n-push",
        "EXAMPLES/skills-n8n/n8n-seed-db": ".claude/skills/n8n-seed-db",
        "EXAMPLES/skills-n8n/n8n-deploy": ".claude/skills/n8n-deploy",
    },
    "keep_reason": "n8n full stack — copie skills n8n depuis EXAMPLES, retire RUNBOOK (créé post-prod)",
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

# bdd-migration : copie le skill db-migration (Alembic) depuis EXAMPLES (hors cœur)
BDD_MIGRATION = {
    "delete": [
        "workflows/",
    ],
    "copy_examples": {
        # db-migration est stack-spécifique (Alembic) → vit dans EXAMPLES, copié à la demande
        "EXAMPLES/skills-db/db-migration": ".claude/skills/db-migration",
    },
    "keep_reason": "BDD migration — copie le skill db-migration (Alembic) depuis EXAMPLES/skills-db",
}

PROFILES = {
    "script-jetable": SCRIPT_JETABLE,
    "automation-n8n": AUTOMATION_N8N,
    "python-app": PYTHON_APP,
    "web-app": WEB_APP,
    "bdd-migration": BDD_MIGRATION,
}


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

    # Copy EXAMPLES si demandé par le profil (ex: automation-n8n copie skills n8n)
    copy_examples = profile.get("copy_examples", {})
    if copy_examples:
        copy_from_examples(root, copy_examples, dry_run)

    # Post-cleanup : retirer les @-imports cassés de CLAUDE.md
    if not dry_run:
        fix_claude_md_imports(root)

    return 0


def copy_from_examples(root: Path, mapping: dict, dry_run: bool) -> None:
    """Copie des dossiers depuis EXAMPLES/ vers le projet selon le profil."""
    for src_rel, dst_rel in mapping.items():
        src = root / src_rel
        dst = root / dst_rel

        if not src.exists():
            print(f"  ⚠️  EXAMPLES source absente : {src_rel} (skip)")
            continue

        if dst.exists():
            print(f"  ⚠️  Destination déjà existante : {dst_rel} (skip pour éviter écrasement)")
            continue

        if dry_run:
            print(f"  [DRY] Would copy : {src_rel} → {dst_rel}")
        else:
            try:
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                print(f"  📦 Copied EXAMPLE : {src_rel} → {dst_rel}")
            except Exception as e:
                print(f"  ⚠️  Échec copie {src_rel} : {e}", file=sys.stderr)


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
