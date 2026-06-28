# Changelog — Sync ERP→Notion

Format : [Keep a Changelog](https://keepachangelog.com/). Versionning : `vYYYY.MM.DD-HHMM` (tag de déploiement).

## [Unreleased]

### Added

- Client SAP B1 (auth + fetch orders + pagination) — spec [001-erp-connector](conception/specs/001-erp-connector/spec.md)
- Tests unitaires SAP connector (12 tests, coverage 87%)

### Changed

- Retry pattern : `tenacity` au lieu de retry maison (plus robuste)

## [v2026.05.22-1500] — 2026-05-22

### Added

- Structure projet initiale (CLAUDE.md, docs/, specs/, src/)
- Setup CI GitHub Actions (lint + tests)
- Pre-commit hooks (ruff, gitleaks)

### Decided

- Stack : n8n on-prem + Python helpers ([ADR-0001](adr/0001-mvp-stack-n8n-python.md))
- Auth ERP : session token rotatif ([ADR-0002](adr/0002-mvp-auth-session-token-sap.md))
- Stockage delta : n8n Data Tables ([ADR-0003](adr/0003-mvp-storage-n8n-data-tables.md))

## [v2026.05.20-1700] — 2026-05-20

### Added

- Kickoff projet ACME
- Brief + objectifs validés avec Marie
- Repo Git initialisé

---

## Conventions

- **Added** : nouvelle feature
- **Changed** : modification d'une feature existante
- **Deprecated** : feature qui va disparaître
- **Removed** : feature supprimée
- **Fixed** : bug fix
- **Security** : correctif de sécurité
- **Decided** : décision tech structurante (lien vers ADR)

Bugs fixés et features livrées vont **dans le même fichier** (pas de bugs log séparé).
