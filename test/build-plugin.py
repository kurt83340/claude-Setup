#!/usr/bin/env python3
"""build-plugin.py — Assemble un plugin Claude Code distribuable À PARTIR du template
standalone, SANS toucher au template (qui reste utilisable en `.claude/` standalone).

Le layout plugin diffère du standalone :
  standalone            → plugin (root)
  .claude/skills/*      → skills/*
  .claude/agents/*      → agents/*
  .claude/hooks/*.py|sh → hooks/*  (+ hooks/hooks.json généré depuis settings.json)
  settings.json "hooks" → hooks/hooks.json (chemins ${CLAUDE_PROJECT_DIR}/.claude/hooks → ${CLAUDE_PLUGIN_ROOT}/hooks)

Usage : python3 test/build-plugin.py --root . --out <dir> [--name juperso-template]
Réf : https://code.claude.com/docs/en/plugins
"""
import argparse, json, shutil, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", default="juperso-template")
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()

    root = args.root.resolve()
    claude = root / ".claude"
    if not claude.exists():
        print("❌ .claude/ introuvable — lance depuis la racine du template", file=sys.stderr)
        return 1

    out = args.out.resolve() / args.name
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)

    # 1. Manifeste
    manifest = {
        "name": args.name,
        "description": "Template Claude Code solo-dev/client (Spec-Driven Dev + doc-as-memory) : "
                       "skills handoff/spec/feature-done/adr/lecon/idee/doc-health/codemap/pivot/"
                       "db-migration, agent doc-maintainer, hooks lifecycle.",
        "version": args.version,
        "author": {"name": "Julien Leroy"},
    }
    (out / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {"skills": 0, "agents": 0, "hook_scripts": 0, "hook_events": 0}

    # 2. skills/ (chaque dossier de skill, à plat)
    src_skills = claude / "skills"
    if src_skills.exists():
        for d in sorted(src_skills.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                shutil.copytree(d, out / "skills" / d.name)
                summary["skills"] += 1

    # 3. agents/
    src_agents = claude / "agents"
    if src_agents.exists():
        dst = out / "agents"; dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_agents.glob("*.md")):
            shutil.copy2(f, dst / f.name); summary["agents"] += 1

    # 4. hooks/ (scripts + hooks.json transformé)
    src_hooks = claude / "hooks"
    dst_hooks = out / "hooks"; dst_hooks.mkdir(parents=True, exist_ok=True)
    if src_hooks.exists():
        for f in sorted(src_hooks.iterdir()):
            if f.is_file() and f.suffix in (".py", ".sh"):
                shutil.copy2(f, dst_hooks / f.name); summary["hook_scripts"] += 1

    settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
    hooks_obj = settings.get("hooks", {})
    # Rewrite des chemins standalone → plugin
    blob = json.dumps({"hooks": hooks_obj}, indent=2, ensure_ascii=False)
    blob = blob.replace("${CLAUDE_PROJECT_DIR}/.claude/hooks/", "${CLAUDE_PLUGIN_ROOT}/hooks/")
    (dst_hooks / "hooks.json").write_text(blob + "\n", encoding="utf-8")
    summary["hook_events"] = len(hooks_obj)

    # README plugin
    (out / "README.md").write_text(
        f"# {args.name}\n\nPlugin Claude Code généré depuis le template standalone.\n\n"
        f"## Installer\n\n```\n/plugin marketplace add <toi>/<repo>\n/plugin install {args.name}@<repo>\n```\n\n"
        f"## Tester en local\n\n```\nclaude --plugin-dir ./{args.name}\n```\n\n"
        f"Skills invoqués en `/{args.name}:<skill>`. Régénérer : `python3 test/build-plugin.py --out dist`.\n",
        encoding="utf-8")

    print(f"✅ Plugin assemblé : {out}")
    print(f"   skills={summary['skills']} agents={summary['agents']} "
          f"hook_scripts={summary['hook_scripts']} hook_events={summary['hook_events']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
