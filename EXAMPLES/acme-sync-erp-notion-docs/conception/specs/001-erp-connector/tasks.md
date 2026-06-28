# Tasks — 001 ERP Connector

Checklist d'implémentation. Mise à jour au fur et à mesure.

## Tasks

- [x] **#1** Setup module `src/sap_connector/` + `__init__.py` exports
- [x] **#2** Implémenter `_http.py` (wrapper httpx avec retry tenacity)
- [x] **#3** Implémenter `AuthManager` (login + cache token)
- [x] **#4** Implémenter `SapClient.get_orders_since()` avec pagination
- [x] **#5** Tests unitaires `auth.py` + `_http.py` (respx mocks)
- [ ] **#6** Implémenter `SapClient.get_order_lines()`
- [ ] **#7** Ajouter logging structuré (structlog) sur toutes méthodes publiques
- [ ] **#8** Tests d'intégration sur staging ACME (VPN requis)

## Validation finale (DoD)

- [ ] Tous tests verts (`pytest tests/unit/test_sap_connector.py`)
- [ ] Coverage >= 80% (`pytest --cov=sap_connector --cov-fail-under=80`)
- [ ] Lint clean (`ruff check src/sap_connector/`)
- [ ] Type check clean (`mypy --strict src/sap_connector/`)
- [ ] Doc à jour : `docs/conception/ARCHITECTURE.md` (section module sap_connector)
- [ ] Entry CHANGELOG ajoutée
- [ ] PR créée avec lien vers cette spec

## Notes

- Task #8 bloquée tant que VPN ACME instable (voir HANDOFF)
- Si task #6 plus longue que prévu, ouvrir un thread Slack avec Paul pour clarifier le schéma DocumentLines
