#!/usr/bin/env python3
"""
PreCompact hook — Snapshot d'état avant compaction (cache non-versionné, par-session).

Pattern inspiré de github.com/thepushkarp/handoff.

Trigger : avant que Claude compacte le contexte (auto à ~90% OU /compact manuel).
Action :
  1. Lire le transcript (extraire les derniers messages user)
  2. Lire git status + log
  3. Écrire (OVERWRITE) le snapshot dans
     .claude/.cache/handoff-snapshot-<session_id>.md — cache gitignored, nommé
     par session_id (pas de collision entre teammates partageant le repo), jamais appendé.
  4. Écrire marker /tmp/claude-handoff-marker-<session_id>.json pour SessionStart

Input stdin (JSON Claude Code hook event) :
  {
    "session_id": "...",
    "transcript_path": "/path/to/transcript.jsonl",
    "cwd": "/path/to/project",
    "trigger": "auto" | "manual"   # top-level — PreCompact n'a PAS de tool_input
  }
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def run(cmd: str, cwd: str = None) -> str:
    """Exécute un shell command, retourne stdout (trimmed)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""


def extract_last_user_messages(transcript_path: str, n: int = 3) -> list:
    """Extrait les n derniers messages user du transcript JSONL."""
    user_msgs = []
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "user":
                        content = entry.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            content = " ".join(
                                c.get("text", "") for c in content if c.get("type") == "text"
                            )
                        user_msgs.append(content[:300])
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return user_msgs[-n:]


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", os.getcwd())
    # PreCompact porte "trigger" au TOP-LEVEL ("auto"|"manual"). Il n'a PAS de
    # tool_input (réservé aux events Pre/PostToolUse) — d'où le bug historique.
    trigger = data.get("trigger", "auto")

    # Snapshot écrit dans un cache NON-VERSIONNÉ (.claude/.cache/, gitignored) au lieu
    # d'être appendé au HANDOFF.md versionné (sinon bloat : +~442 o/compaction, jamais purgé).
    if not (Path(cwd) / ".claude").exists():
        sys.exit(0)
    cache_dir = Path(cwd) / ".claude" / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Nom par-session → deux teammates partageant le repo n'écrasent pas le snapshot
    # l'un de l'autre (sinon ré-injection du mauvais contexte au SessionStart).
    safe_sid = "".join(c if (c.isalnum() or c in "-_") else "_" for c in session_id)
    snapshot_path = cache_dir / f"handoff-snapshot-{safe_sid}.md"

    # Git state
    branch = run("git branch --show-current", cwd=cwd) or "unknown"
    status = run("git status --short", cwd=cwd) or "(clean)"
    log = run("git log -5 --oneline", cwd=cwd) or "(no commits)"

    # Derniers messages user
    user_msgs = extract_last_user_messages(transcript_path) if transcript_path else []

    # Construire la section snapshot (écrite en overwrite plus bas)
    now = datetime.now().strftime("%Y-%m-%d %Hh%M")
    snapshot = f"""

---

## 📸 Auto-snapshot pré-compaction ({trigger}) — {now}

**Branche** : `{branch}`
**Session ID** : `{session_id[:8]}…`

### Git status
```
{status}
```

### 5 derniers commits
```
{log}
```

### Derniers messages user (extraits)
{chr(10).join(f"- {m}" for m in user_msgs) if user_msgs else "_(aucun)_"}
"""

    # Overwrite (pas d'append) → le cache ne contient jamais qu'UN snapshot, le dernier.
    try:
        snapshot_path.write_text(snapshot, encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Failed to write snapshot: {e}", file=sys.stderr)
        sys.exit(0)

    # Marker pour SessionStart
    marker_path = Path(tempfile.gettempdir()) / f"claude-handoff-marker-{session_id}.json"
    marker_path.write_text(
        json.dumps(
            {
                "needs_inject": True,
                "snapshot_path": str(snapshot_path),
                "timestamp": now,
                "trigger": trigger,
            }
        )
    )

    # Notification user (non-blocking)
    print(
        json.dumps(
            {
                "systemMessage": f"📸 Snapshot pré-compaction écrit dans .claude/.cache/ (trigger: {trigger}). HANDOFF.md versionné non touché. Re-injection au prochain start."
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
