#!/usr/bin/env python3
"""Helpers partagés des hooks de snapshot (PreCompact + SessionEnd).

Même dossier que les hooks → `import snapshot_common` fonctionne tel quel
(sys.path[0] = dossier du script exécuté). Source unique du format de snapshot
et de l'extraction git/transcript — ne pas dupliquer dans les hooks.
"""

import json
import subprocess
from datetime import datetime


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


def build_snapshot(
    kind: str, label: str, session_id: str, transcript_path: str, cwd: str
) -> str:
    """Compose un snapshot markdown : git state + derniers messages user.

    kind  : "pré-compaction" | "fin de session" (rendu dans le header)
    label : trigger PreCompact ("auto"/"manual") ou reason SessionEnd ("logout"…)
    """
    branch = run("git branch --show-current", cwd=cwd) or "unknown"
    status = run("git status --short", cwd=cwd) or "(clean)"
    log = run("git log -5 --oneline", cwd=cwd) or "(no commits)"
    user_msgs = extract_last_user_messages(transcript_path) if transcript_path else []
    now = datetime.now().strftime("%Y-%m-%d %Hh%M")

    return f"""

---

## 📸 Auto-snapshot {kind} ({label}) — {now}

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
