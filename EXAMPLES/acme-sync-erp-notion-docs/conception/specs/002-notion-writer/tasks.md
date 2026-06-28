# Tasks — 002 Notion Writer

## Tasks

- [ ] **#1** Setup module `src/notion_writer/`
- [ ] **#2** Implémenter `RateLimiter` + tests
- [ ] **#3** Implémenter `NotionWriter.__init__` + `validate_schema()`
- [ ] **#4** Implémenter `mapping.py` (sap → notion props)
- [ ] **#5** Implémenter `upsert_order()` (create + update detection)
- [ ] **#6** Tests unitaires complets (mock notion-client)
- [ ] **#7** Test d'intégration sur DB Notion staging

## DoD

- [ ] Tous tests verts
- [ ] Coverage >= 80%
- [ ] Lint + mypy clean
- [ ] `docs/conception/ARCHITECTURE.md` MAJ (section notion_writer)
- [ ] CHANGELOG MAJ
- [ ] PR avec lien spec

## Bloqueurs potentiels

- Attente partage DB Notion par Marie (voir ACCESS.md)
- Si Marie change le schema DB en cours de route → revoir mapping
