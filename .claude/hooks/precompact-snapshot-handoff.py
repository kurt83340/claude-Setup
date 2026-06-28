#!/usr/bin/env python3
"""
PreCompact hook — Snapshot HANDOFF.md avant compaction.

Pattern inspiré de github.com/thepushkarp/handoff.

Trigger : avant que Claude compacte le contexte (auto à ~90% OU /compact manuel).
Action :
  1. Lire le transcript (extraire last user/assistant messages)
  2. Lire git status + log + diff
  3. Append section snapshot à .claude/docs/HANDOFF.md avec timestamp
  4. Écrire marker /tmp/claude-handoff-marker-<session_id>.json pour SessionStart

Input stdin (JSON Claude Code hook event) :
  {
    "session_id": "...",
    "transcript_path": "/path/to/transcript.jsonl",
    "cwd": "/path/to/project",
    "tool_input": {"trigger": "auto" | "manual"}
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


def extract_last_messages(transcript_path: str, n: int = 3) -> dict:
    """Extrait les derniers messages user et assistant du transcript JSONL."""
    user_msgs = []
    assistant_msgs = []
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
                    elif entry.get("type") == "assistant":
                        content = entry.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            content = " ".join(
                                c.get("text", "") for c in content if c.get("type") == "text"
                            )
                        assistant_msgs.append(content[:300])
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return {
        "user": user_msgs[-n:],
        "assistant": assistant_msgs[-n:],
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", os.getcwd())
    trigger = data.get("tool_input", {}).get("trigger", "auto")

    # Snapshot écrit dans un cache NON-VERSIONNÉ (.claude/.cache/, gitignored) au lieu
    # d'être appendé au HANDOFF.md versionné (sinon bloat : +~442 o/compaction, jamais purgé).
    if not (Path(cwd) / ".claude").exists():
        sys.exit(0)
    cache_dir = Path(cwd) / ".claude" / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = cache_dir / "handoff-snapshot.md"

    # Git state
    branch = run("git branch --show-current", cwd=cwd) or "unknown"
    status = run("git status --short", cwd=cwd) or "(clean)"
    log = run("git log -5 --oneline", cwd=cwd) or "(no commits)"

    # Last messages
    messages = (
        extract_last_messages(transcript_path) if transcript_path else {"user": [], "assistant": []}
    )

    # Append snapshot section
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
{chr(10).join(f"- {m}" for m in messages["user"]) if messages["user"] else "_(aucun)_"}

### TODO Model Summary (à remplir au prochain SessionStart)
- [ ] Status courant : ...
- [ ] Échecs tentés : ...
- [ ] Next steps : ...

### TODO Handoff Context (à remplir)
- [ ] ...
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
