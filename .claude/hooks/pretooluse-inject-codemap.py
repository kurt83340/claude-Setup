#!/usr/bin/env python3
"""
PreToolUse hook (matcher: "Edit|Write") — Injecte les contraintes non-déductibles avant édition de code.

Pourquoi : Claude retrouve seul le rôle/les imports/les tests d'un fichier (agentic search).
Ce qu'il NE PEUT PAS deviner, ce sont les *règles de couplage* (« ne jamais importer X »),
l'*intention* et les *gotchas*. C'est ça — et seulement ça — qu'on réinjecte avant une édition,
pour qu'il ne viole pas une contrainte d'architecture qu'aucune lecture de code ne révèle.

Trigger : avant chaque Edit/Write sur un fichier de code (src/, lib/, app/, tests/).
Action :
  1. Vérifier que le fichier est du code (sinon skip)
  2. Lire .claude/docs/code-map.md
  3. Extraire les sections "Règles de couplage", "Intention & décisions locales", "Gotchas"
  4. Retourner en additionalContext

NB : on n'injecte PAS de description fichier-par-fichier (déductible + périssable).

Input stdin :
  {"tool_name": "Edit"|"Write", "tool_input": {"file_path": "..."}, "cwd": "..."}

Output JSON :
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}
"""

import json
import os
import re
import sys
from pathlib import Path

# Limite chars pour additionalContext (max 10k, on cap à 4k pour rester safe)
MAX_CHARS = 4000

# Titres des sections non-déductibles à réinjecter (matche le code-map.md du template)
SECTION_TITLES = [
    "Règles de couplage",
    "Intention & décisions locales",
    "Gotchas",
]


def extract_sections(codemap_text: str) -> str:
    """Extrait les sections non-déductibles (couplage / intention / gotchas)."""
    chunks = []
    for title in SECTION_TITLES:
        # Capture "## <title> ..." jusqu'au prochain "## " ou la fin
        pattern = re.compile(
            rf"(##\s+{re.escape(title)}.*?)(?=\n##\s|\Z)", re.DOTALL
        )
        m = pattern.search(codemap_text)
        if m:
            chunks.append(m.group(1).strip())
    return "\n\n".join(chunks)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Gate : seulement pour fichiers code (pas .md, pas config)
    if not any(
        seg in file_path for seg in ["/src/", "/tests/", "/lib/", "/app/"]
    ) or file_path.endswith((".md", ".json", ".yaml", ".yml", ".toml")):
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    codemap_path = Path(cwd) / ".claude" / "docs" / "code-map.md"

    if not codemap_path.exists():
        sys.exit(0)

    try:
        codemap_text = codemap_path.read_text(encoding="utf-8")
    except Exception:
        sys.exit(0)

    sections = extract_sections(codemap_text)
    if not sections:
        sys.exit(0)

    context = f"""## 🗺️  Code Map — contraintes à respecter pour ce fichier

Tu vas éditer `{file_path}`. Voici ce que la code-map impose et que tu ne peux PAS
deviner en lisant le code (règles de couplage, intention, gotchas) :

{sections[:MAX_CHARS]}

⚠️  Respecte les **règles de couplage** ci-dessus. Le rôle du fichier, ses imports
et ses tests : retrouve-les directement dans le code (grep/lecture)."""

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
