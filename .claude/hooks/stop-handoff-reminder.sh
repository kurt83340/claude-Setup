#!/usr/bin/env bash
# Stop hook — Rappel /handoff si HANDOFF.md est stale (> 1 jour).
#
# Trigger : à chaque fin de tour Claude (event Stop).
# Action :
#   - Vérifier l'âge de .claude/docs/HANDOFF.md
#   - Si > 24h ET il y a eu des changements git → suggérer /handoff
#
# Non-blocking (juste systemMessage).
#
# ── MULTI-AGENT / lead-only (à lire) ────────────────────────────────────────
# Le but est qu'UN SEUL rappel parte (celui du lead), pas N (un par teammate)
# sur le même HANDOFF.md partagé. Ce qui est vrai d'après la doc des hooks :
#   • L'event Stop ne se déclenche QUE pour l'agent principal (le lead). Les
#     sous-agents/teammates déclenchent SubagentStop — qu'on ne câble PAS.
#     → Si les teammates sont des sous-agents, ZÉRO spam : ce hook ne tourne
#       que pour le lead. C'est la garantie principale.
#   • Stop ne porte PAS de champ "agent_type" (réservé à SubagentStop). Donc
#     si des teammates tournent comme des SESSIONS top-level indépendantes
#     partageant le repo, on ne peut PAS les distinguer du lead depuis la
#     payload. Honnêtement : non détectable ici.
# Leviers fournis :
#   • Gate défensif sur agent_type SI jamais présent (compat future / SubagentStop).
#   • Variable d'env CLAUDE_HANDOFF_REMINDER=0|off|false|no → coupe le rappel
#     (à exporter dans le lanceur des sessions teammate pour le cas top-level).
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Levier explicite de désactivation (cas teammates = sessions indépendantes).
case "${CLAUDE_HANDOFF_REMINDER:-}" in
  0 | off | false | no | OFF | FALSE | NO) exit 0 ;;
esac

# Lire stdin JSON (Claude Code hook event)
INPUT=$(cat)

# Parsing PORTABLE via python3 (pas de grep -oP, GNU-only / absent sur macOS).
# Extrait cwd + agent_type, séparés par une tabulation.
PARSED=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
cwd = d.get("cwd") or ""
agent = d.get("agent_type") or d.get("agentType") or ""
sys.stdout.write(cwd + "\t" + agent)
' 2>/dev/null || printf '\t')

CWD="${PARSED%%$'\t'*}"
AGENT="${PARSED#*$'\t'}"
if [ -z "$CWD" ]; then CWD="$PWD"; fi

# Gate lead-only défensif : si agent_type est présent ET n'est pas le lead,
# c'est un teammate/sous-agent → on sort sans rappeler. (Stop n'expose
# normalement pas ce champ ; absent ⇒ on suppose le lead et on continue.)
case "$AGENT" in
  "" | lead | main) : ;; # lead présumé → continuer
  *) exit 0 ;;           # teammate / sous-agent identifié → pas de rappel
esac

HANDOFF="$CWD/.claude/docs/HANDOFF.md"

if [ ! -f "$HANDOFF" ]; then
  exit 0
fi

# Âge en secondes
NOW=$(date +%s)
MTIME=$(stat -c %Y "$HANDOFF" 2>/dev/null || stat -f %m "$HANDOFF" 2>/dev/null || echo "$NOW")
AGE_SEC=$((NOW - MTIME))
AGE_HOURS=$((AGE_SEC / 3600))

# Seuil : 24h
if [ "$AGE_HOURS" -lt 24 ]; then
  exit 0
fi

# Vérifier qu'il y a des changements git (sinon rappel inutile)
cd "$CWD" 2>/dev/null || exit 0
if [ -z "$(git status --short 2>/dev/null)" ]; then
  exit 0  # rien changé, pas la peine de rappeler
fi

# Non-blocking notification
echo "{\"systemMessage\": \"⏰ HANDOFF.md date de ${AGE_HOURS}h. Pense à /handoff avant la fin de session.\"}"
exit 0
