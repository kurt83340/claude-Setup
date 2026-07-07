#!/usr/bin/env python3
"""
Hooks TaskCreated / TaskCompleted / TeammateIdle — trace de progression d'équipe.

Append 1 ligne JSON par événement dans .claude/.cache/team-progress.log (non-versionné).
Suivi lisible pendant une session /team : tail -f .claude/.cache/team-progress.log

Toujours exit 0 : ne bloque JAMAIS une action d'équipe (exit 2 annulerait la création /
complétion de task ou stopperait le teammate). Les payloads de ces events ne sont pas
détaillés dans la doc → on logge défensivement les champs présents.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd") or os.getcwd()
    if not (Path(cwd) / ".claude").exists():
        sys.exit(0)

    try:
        cache_dir = Path(cwd) / ".claude" / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": data.get("hook_event_name", "unknown"),
        }
        # Champs plats connus/probables — loggés seulement s'ils existent
        for key in ("teammate_name", "team_name", "session_id", "task_id", "subject", "status", "owner"):
            if data.get(key):
                entry[key] = data[key]
        # Variante : task imbriquée
        task = data.get("task")
        if isinstance(task, dict):
            for key in ("id", "subject", "status", "owner"):
                if task.get(key):
                    entry[f"task_{key}"] = task[key]

        with open(cache_dir / "team-progress.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # trace best-effort, jamais bloquant

    sys.exit(0)


if __name__ == "__main__":
    main()
