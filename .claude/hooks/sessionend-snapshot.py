#!/usr/bin/env python3
"""
SessionEnd hook — filet « n'oublie rien » : snapshot d'état à CHAQUE fin de session.

Si la session se ferme sans /handoff, ce snapshot sera réinjecté au prochain démarrage
(SessionStart source=startup, via sessionstart-inject-handoff.py) S'IL est plus frais
que HANDOFF.md — puis consommé. SessionEnd ne peut PAS injecter de contexte lui-même
(event cleanup-only, doc officielle) — d'où le duo écriture-ici / injection-au-startup.

Écrit : .claude/.cache/session-end-snapshot.md (non-versionné, OVERWRITE — 1 par checkout).
Multi-sessions sur le MÊME checkout : last-write-wins, assumé (c'est un filet, pas la
source de vérité ; chaque worktree a son .cache/ donc son propre filet).

Input stdin :
  {
    "session_id": "...",
    "transcript_path": "...",
    "cwd": "/path/to/project",
    "reason": "clear" | "resume" | "logout" | "prompt_input_exit" | "other"
  }
"""

import json
import os
import sys
from pathlib import Path

from snapshot_common import build_snapshot


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", os.getcwd())
    reason = data.get("reason", "other")

    if not (Path(cwd) / ".claude").exists():
        sys.exit(0)

    try:
        cache_dir = Path(cwd) / ".claude" / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot = build_snapshot("fin de session", reason, session_id, transcript_path, cwd)
        (cache_dir / "session-end-snapshot.md").write_text(snapshot, encoding="utf-8")
    except Exception:
        pass  # filet best-effort : ne jamais gêner la fermeture de session

    sys.exit(0)


if __name__ == "__main__":
    main()
