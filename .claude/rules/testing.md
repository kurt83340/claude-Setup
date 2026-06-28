# Testing

## Outils

- Framework : `pytest`
- Coverage : `pytest-cov` (objectif **80% minimum**)
- Fixtures : `tests/fixtures/`
- Mocks API externes : `respx` (pour httpx), pas `unittest.mock` brut

## Structure

```
tests/
├── unit/              # tests rapides, sans I/O
├── integration/       # avec BDD réelle (testcontainers)
├── e2e/               # workflow complet sync (slow, < 5/jour)
└── fixtures/
    ├── sap_responses/
    └── notion_responses/
```

## Règles

- Test = miroir du module (`src/sap_client.py` → `tests/unit/test_sap_client.py`)
- 1 test = 1 assertion principale (lisibilité)
- Pas de mocks pour la BDD → testcontainers Postgres
- Pas de tests qui dépendent d'API externes en CI (utiliser respx)
- Tous les tests doivent passer avant push (pre-commit hook)

## Lancer

```bash
pytest                    # tous les tests
pytest tests/unit/        # juste unit
pytest -m "not slow"      # skip les lents
pytest --cov --cov-report=html
```
