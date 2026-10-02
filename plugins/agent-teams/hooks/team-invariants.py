#!/usr/bin/env python3
"""
Hooks PreToolUse(Agent|Task) + SessionStart(compact|clear) — invariants d'équipe juste-à-temps (v1.2.0).

Avant : l'activation copiait une rule dans `.claude/rules/agent-teams.md`, chargée par CHAQUE session
du projet (~1,9k tokens), même sans équipe. Maintenant rien n'est chargé au démarrage ; les invariants
(`skills/team/invariants.md`) arrivent au moment où une équipe se forme :

- un appel `Agent` avec `name` lance un teammate quand le flag est actif (doc agent teams : « Claude
  launches a teammate when it calls the Agent tool with a name while agent teams are enabled, unless
  the call is a fork or passes isolation ») → § Teammate est ajouté à la FIN du prompt de spawn
  (`updatedInput`) : le teammate le reçoit, rôle préconfiguré ou ad-hoc ; le contexte du lead ne grossit pas ;
- au 1er spawn de la session, § Lead est injecté au lead (`additionalContext`), une seule fois
  (marqueur par session dans $TMPDIR), ré-armé après compaction ou /clear (SessionStart).

Rien n'est fait : flag inactif (le spawn reste un subagent), appel sans `name`, fork, `isolation`,
ou appel émis DANS un subagent/teammate (`agent_id` présent — pas d'équipe imbriquée).
Toujours exit 0, jamais de `permissionDecision` : le flux de permissions normal continue.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

INVARIANTS = Path(__file__).resolve().parent.parent / "skills" / "team" / "invariants.md"
TEAM_ENV = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
TEAMMATE_HEAD = "## § Teammate — règles d'équipe (ajoutées par le plugin agent-teams)"


def teams_enabled() -> bool:
    return os.environ.get(TEAM_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def lead_marker(session_id) -> Path:
    sid = re.sub(r"[^\w.-]", "_", str(session_id or "nosession"))
    return Path(tempfile.gettempdir()) / f"claude-agent-teams-lead-{sid}.flag"


def section(text: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def emit(out: dict) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", **out}}, ensure_ascii=False))


def on_spawn(data: dict) -> None:
    ti = data.get("tool_input")
    if not teams_enabled() or data.get("agent_id") or not isinstance(ti, dict):
        return
    if not ti.get("name") or ti.get("isolation") or ti.get("subagent_type") == "fork":
        return
    try:
        text = INVARIANTS.read_text(encoding="utf-8")
    except OSError:
        text = ""
    teammate, lead = section(text, "§ Teammate"), section(text, "§ Lead")
    if not (teammate and lead):  # plugin abîmé : le dire, jamais d'équipe sans protocole en silence
        emit({"additionalContext": f"⚠️ Plugin agent-teams : invariants illisibles ({INVARIANTS}) — "
                                   "le teammate part SANS règles d'équipe. Dis-le à l'utilisateur et propose "
                                   "de réinstaller le plugin (`/plugin marketplace update claude-setup`)."})
        return
    out = {}
    prompt = str(ti.get("prompt", ""))
    if TEAMMATE_HEAD not in prompt:  # déjà présent : respawn avec un prompt recopié
        out["updatedInput"] = {**ti, "prompt": f"{prompt.rstrip()}\n\n---\n\n{TEAMMATE_HEAD}\n\n{teammate}\n"}
    marker = lead_marker(data.get("session_id"))
    if not marker.exists():
        out["additionalContext"] = f"## 🧑‍🤝‍🧑 Agent teams — § Lead (plugin agent-teams)\n\n{lead}"
        try:
            marker.touch()
        except OSError:
            pass
    if out:
        emit(out)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(data, dict):
        sys.exit(0)
    if data.get("hook_event_name") == "SessionStart":
        try:  # contexte résumé ou vidé → § Lead redonné au prochain spawn
            lead_marker(data.get("session_id")).unlink()
        except OSError:
            pass
    else:
        on_spawn(data)
    sys.exit(0)


if __name__ == "__main__":
    main()
