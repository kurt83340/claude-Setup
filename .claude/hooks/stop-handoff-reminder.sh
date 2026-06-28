#!/usr/bin/env bash
# Stop hook — Rappel /handoff si HANDOFF.md est stale (> 1 jour).
#
# Trigger : à chaque fin de tour Claude.
# Action :
#   - Vérifier l'âge de .claude/docs/HANDOFF.md
#   - Si > 24h ET il y a eu des changements git → suggérer /handoff
#
# Non-blocking (juste systemMessage).

set -euo pipefail

# Lire stdin JSON (Claude Code hook event)
INPUT=$(cat)

# Extraire cwd
CWD=$(echo "$INPUT" | grep -oP '"cwd"\s*:\s*"\K[^"]+' || echo "$PWD")

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
