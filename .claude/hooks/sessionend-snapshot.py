#!/usr/bin/env python3
"""
SessionEnd hook — filet « n'oublie rien » : snapshot d'état quand une session se ferme
SANS /handoff alors qu'elle a laissé une trace git.

Le snapshot est réinjecté au prochain démarrage (SessionStart source=startup, via
sessionstart-inject-handoff.py) puis consommé. SessionEnd ne peut PAS injecter de contexte
lui-même (event cleanup-only, doc officielle) — d'où le duo écriture-ici / injection-au-startup.

Quand NE PAS écrire (v1.5.0 — avant, le filet partait à CHAQUE fin de session : SessionEnd
passe toujours APRÈS /handoff, donc le snapshot était toujours « plus frais » que HANDOFF.md
→ fausse alerte « session fermée sans /handoff » à chaque démarrage) :
  1. HANDOFF.md modifié PENDANT la session (/handoff fait) → rien à rattraper ; un ancien
     filet est périmé → supprimé.
  2. Session sans trace git (même HEAD, même état de l'arbre qu'au démarrage : question,
     lecture, revue…) → rien à rattraper.
Début de session = marqueur posé par SessionStart (startup/resume/clear), à défaut la 1re
entrée datée du transcript.

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

from snapshot_common import (build_snapshot, git_fingerprint, pop_session_start,
                             transcript_started_at)


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

    cache_dir = Path(cwd) / ".claude" / ".cache"
    net = cache_dir / "session-end-snapshot.md"
    try:
        start = pop_session_start(cwd, session_id)
        started_at = start.get("t") if start else None
        if started_at is None and transcript_path:
            started_at = transcript_started_at(transcript_path)

        handoff = Path(cwd) / ".claude" / "docs" / "HANDOFF.md"
        if started_at is not None and handoff.is_file() \
                and handoff.stat().st_mtime >= started_at:
            # Cas 1 : /handoff fait pendant la session → pas de filet, l'ancien est périmé.
            try:
                net.unlink()
            except OSError:
                pass
            sys.exit(0)

        if start and start.get("git") and start["git"] == git_fingerprint(cwd):
            sys.exit(0)  # Cas 2 : session sans trace git → rien à rattraper

        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot = build_snapshot("fin de session", reason, session_id, transcript_path, cwd)
        net.write_text(snapshot, encoding="utf-8")
    except Exception:
        pass  # filet best-effort : ne jamais gêner la fermeture de session

    sys.exit(0)


if __name__ == "__main__":
    main()
