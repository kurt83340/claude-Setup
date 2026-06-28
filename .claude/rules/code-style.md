---
paths: "**/*.py"
---

# Code style — Python

## Outils

- Formatter : `ruff format`
- Linter : `ruff check --fix`
- Type checker : `mypy --strict`
- Lancer avant commit : `make lint` (déjà dans pre-commit hook)

## Conventions

- Python 3.12+, type hints obligatoires (signatures publiques)
- Imports : isort via ruff
- Docstrings : Google style, uniquement sur fonctions publiques
- Longueur ligne : 100 chars
- f-strings > `.format()` > `%`

## Naming

- `snake_case` pour variables/fonctions
- `PascalCase` pour classes
- `UPPER_CASE` pour constantes module
- Pas de préfixe `_` sauf vraie privacy (rare)

## Erreurs

- Lever des exceptions custom (`AcmeSyncError`, `SapApiError`, etc.)
- JAMAIS de `except Exception:` nu — toujours typer
- Logging structuré (JSON) via `structlog`, pas `print`
