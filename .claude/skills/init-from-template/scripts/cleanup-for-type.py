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
        ".claude/skills/feature/",
        ".claude/skills/spec/",
        ".claude/skills/pivot/",
        ".claude/skills/idee/",
        ".claude/skills/conception/",
        ".claude/skills/debug/",
        ".claude/skills/scaffold/",
        # (adopt-template : déjà retiré pour tous les types via TEMPLATE_MAINTENANCE)
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

# ── Artefacts de maintenance DU TEMPLATE (retirés en GREENFIELD uniquement) ────
# N'existent que pour développer/distribuer le template lui-même. Un projet GÉNÉRÉ n'en a
# aucun usage — et la self-CI (.github/workflows/ci.yml) teste render.py / l'inventaire, que
# l'init vient justement de supprimer → CI ROUGE héritée. Les plugins stack (plugins/ +
# .claude-plugin/) sont la SOURCE du marketplace : le projet les INSTALLE (/plugin), il ne les
# embarque pas. init-from-template/ est retiré EN DERNIER : il contient CE script (suppression
# OK sous POSIX — le process tourne en mémoire). Réversible : le snapshot git pre-init garde tout.
#
# ⚠️ SÉCURITÉ (bug brownfield 2026-07-07) : .github/, test/, plugins/ existent dans plein de
# VRAIS projets. Chaque dossier n'est supprimé que si sa SENTINELLE template (cf.
# _is_template_owned) prouve qu'il vient bien du template — jamais par homonymie. Et le mode
# --brownfield (/adopt-template) saute ce strip entièrement.
TEMPLATE_MAINTENANCE = [
    ".github/",                            # self-CI + README/CHANGELOG DU template
    "test/",                               # tests + rapports d'audit DU template
    "EXAMPLES/",                           # exemple rempli (acme) — référence, pas du projet
    "plugins/",                            # SOURCE des plugins stack → le projet les installe (marketplace)
    ".claude-plugin/",                     # manifeste marketplace → vit dans le repo template
    ".claude/skills/adopt-template/",      # bootstrap brownfield one-shot (exclusif avec init)
    ".claude/skills/init-from-template/",  # bootstrap one-shot — EN DERNIER (contient ce script)
]


def _is_template_owned(root: Path, rel: str) -> bool:
    """Sentinelles : prouve qu'un dossier de TEMPLATE_MAINTENANCE appartient bien au template
    (et pas au projet de l'utilisateur, qui peut avoir ses propres .github/, test/, plugins/).
    Sentinelle absente → le strip N'Y TOUCHE PAS."""
    if rel == ".github/":
        ci = root / ".github" / "workflows" / "ci.yml"
        try:
            return ci.exists() and "test_hooks" in ci.read_text(encoding="utf-8")
        except Exception:
            return False
    if rel == "test/":
        return (root / "test" / "test_hooks.py").exists()
    if rel == "EXAMPLES/":
        return (root / "EXAMPLES" / "acme-sync-erp-notion-docs").exists()
    if rel in ("plugins/", ".claude-plugin/"):
        return (root / ".claude-plugin" / "marketplace.json").exists()
    return True  # .claude/skills/{init,adopt}-* : noms spécifiques au template


def cleanup(root: Path, profile_name: str, dry_run: bool, brownfield: bool = False) -> int:
    if profile_name not in PROFILES:
        print(f"❌ Type inconnu : {profile_name}", file=sys.stderr)
        print(f"   Types valides : {', '.join(PROFILES.keys())}", file=sys.stderr)
        return 1

    profile = PROFILES[profile_name]
    print(f"📋 Profil : {profile_name}" + (" (mode brownfield /adopt-template)" if brownfield else ""))
    print(f"   {profile['keep_reason']}\n")

    deleted_files = 0
    deleted_dirs = 0
    skipped = 0

    for rel_path in profile["delete"]:
        # Brownfield : le projet EXISTE déjà — ne supprimer que dans .claude/ (scaffold
        # fraîchement rsyncé). Un chemin racine homonyme (workflows/…) peut être à l'user.
        if brownfield and not rel_path.startswith(".claude/"):
            print(f"  ⤳ (brownfield) hors .claude/, non supprimé : {rel_path}")
            skipped += 1
            continue
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

    # Retrait des artefacts de maintenance DU template — greenfield UNIQUEMENT.
    # En brownfield (/adopt-template), .github/, test/, plugins/… sont ceux de l'UTILISATEUR
    # (le rsync d'adopt exclut ceux du template) → on n'y touche JAMAIS.
    if brownfield:
        print("\n🏠 Brownfield : artefacts de maintenance conservés (projet existant) ; "
              "permissions et inventaires non purgés.")
    else:
        strip_template_maintenance(root, dry_run)

    # Post-cleanup : réparer CLAUDE.md + purger settings.json (hooks fantômes + allow-rules mortes)
    if not dry_run:
        fix_claude_md_imports(root)
        prune_dead_hooks(root)
        if not brownfield:
            prune_dead_permissions(root)
            prune_bootstrap_inventory(root)

    return 0


def strip_template_maintenance(root: Path, dry_run: bool) -> int:
    """Retire les artefacts qui ne servent qu'à maintenir LE TEMPLATE (self-CI, tests, exemples,
    plugins source, skills bootstrap — voir TEMPLATE_MAINTENANCE). Greenfield uniquement (jamais
    appelé en --brownfield). Chaque dossier générique n'est supprimé que si sa SENTINELLE prouve
    qu'il vient du template (_is_template_owned) — jamais par homonymie avec un dossier user.
    Réversible via le snapshot git pre-init."""
    print("\n🧹 Artefacts de maintenance du template (inutiles dans un projet généré) :")
    removed = 0
    for rel in TEMPLATE_MAINTENANCE:
        target = root / rel
        if not target.exists():
            continue
        if not _is_template_owned(root, rel):
            print(f"  ⚠️  {rel} : sentinelle template absente → ressemble à un dossier du PROJET, conservé")
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


def prune_bootstrap_inventory(root: Path) -> None:
    """Le strip vient de supprimer les skills bootstrap (init-from-template / adopt-template) :
    retire leurs lignes d'inventaire (puces et lignes de tableau) des index SHIPPÉS — sinon
    chaque projet généré recense 2 skills morts. Greenfield uniquement."""
    pat = re.compile(r"/(?:init-from-template|adopt-template)\b")
    for rel in (".claude/CLAUDE.md", ".claude/rules/template-maintenance.md", "USAGE.md"):
        p = root / rel
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8").split("\n")
        kept = [l for l in lines
                if not (pat.search(l) and l.lstrip().startswith(("-", "|")))]
        removed = len(lines) - len(kept)
        if removed:
            p.write_text("\n".join(kept), encoding="utf-8")
            print(f"🔧 {rel} : {removed} ligne(s) d'inventaire bootstrap retirée(s)")


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
    # Précision avant tout : au moindre doute on GARDE la règle (une allow-rule morte est
    # inoffensive ; une allow-rule vivante supprimée = prompts en boucle / run headless bloqué).
    # - lookbehind : ne pas matcher `.claude/` au milieu d'un chemin (`~/.claude/…`, autre repo)
    # - glob (*?[) dans le chemin : invérifiable par exists() → conserver
    script_re = re.compile(r"(?<![\w~/.\\-])\.claude/[^\s:\"']+\.(?:py|sh)")
    kept, removed = [], 0
    for rule in perms["allow"]:
        m = script_re.search(rule) if isinstance(rule, str) else None
        if m:
            path = m.group(0)
            if not any(c in path for c in "*?[") and not (root / path).exists():
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
    parser.add_argument("--brownfield", action="store_true",
                        help="Mode /adopt-template (projet EXISTANT) : conserve les artefacts de "
                             "maintenance (.github/, test/, plugins/…), ne purge ni permissions ni "
                             "inventaires, et restreint les suppressions de profil à .claude/")
    args = parser.parse_args()

    return cleanup(args.root.resolve(), args.type, args.dry_run, brownfield=args.brownfield)


if __name__ == "__main__":
    sys.exit(main())
