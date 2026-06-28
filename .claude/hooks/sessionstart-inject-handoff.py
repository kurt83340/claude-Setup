#!/usr/bin/env python3
"""
SessionStart hook (matcher: "compact") — Re-inject HANDOFF.md après compaction.

Trigger : quand session démarre AFTER compaction (le matcher "compact" garantit ça).
Action :
  1. Lire le marker /tmp/claude-handoff-marker-<session_id>.json
  2. Si needs_inject=true, lire la dernière section snapshot de HANDOFF.md
  3. Injecter en additionalContext (stdout direct = injection auto par Claude Code)
  4. Flip needs_inject=false dans le marker

Input stdin :
  {
    "session_id": "...",
    "cwd": "/path/to/project",
    "matcher": "compact"
  }
"""

import json
import os
import sys
import tempfile
from pathlib import Path


def read_snapshot(snapshot_path: Path) -> str:
    """Lit le snapshot pré-compaction (cache non-versionné .claude/.cache/)."""
    try:
        return snapshot_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", os.getcwd())

    marker_path = Path(tempfile.gettempdir()) / f"claude-handoff-marker-{session_id}.json"
    if not marker_path.exists():
        # Pas de marker → pas de re-injection nécessaire (session normale)
        sys.exit(0)

    try:
        marker = json.loads(marker_path.read_text())
    except Exception:
        sys.exit(0)

    if not marker.get("needs_inject"):
        sys.exit(0)

    snapshot_path = Path(marker.get("snapshot_path", ""))
    if not snapshot_path.exists():
        sys.exit(0)

    snapshot = read_snapshot(snapshot_path)
    if not snapshot:
        sys.exit(0)

    # Stdout direct = injection auto par Claude Code dans le contexte
    print(
        f"""## 🔄 Re-injection post-compaction

Le contexte vient d'être compacté. Voici le snapshot HANDOFF.md récent pour reprendre où on en était :

{snapshot[:5000]}

→ Lis aussi `.claude/docs/HANDOFF.md` pour l'historique complet si besoin.
→ Continue ton travail. Si tu finis ta session, lance `/handoff` pour propre snapshot."""
    )

    # Flip needs_inject à false
    marker["needs_inject"] = False
    marker_path.write_text(json.dumps(marker))

    sys.exit(0)


if __name__ == "__main__":
    main()
