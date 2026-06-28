# HANDOFF — 2026-05-24 18h45

> Court, narratif, versionné. **Patterns techniques** → auto-memory (Claude le gère).
> **Reprise précise** → utilise `/resume`. Ce fichier = "où j'en suis" pour démarrage à froid.

**Branche** : `feature/001-erp-connector`
**Spec en cours** : [001-erp-connector/](conception/specs/001-erp-connector/spec.md) (5/8 tasks)
**Goal session** : finir le client SAP B1 (auth + fetch orders)

## Status

- ✅ `pytest tests/unit/test_sap_connector.py` (12 tests verts)
- ✅ Lint clean
- ⏳ Tests d'intégration : pas lancés (VPN ACME instable)

## Échecs tentés (à ne pas refaire)

- SDK Python officiel SAP B1 → abandonné (pas maintenu, bugs filtres OData)
- Fetch single-shot sans pagination → KO sur > 20 commandes (SAP limite à 20 par défaut)

## Blocked on

- VPN ACME instable cette semaine → tests E2E reportés
- Marie pas encore partagé la DB Notion avec l'integration (voir ACCESS.md)

## Next (par ordre)

1. **Task #6** : `SapClient.get_order_lines(order_id)`
2. **Task #7** : logging structuré (structlog) sur méthodes publiques
3. **Task #8** : tests d'intégration une fois VPN stable
4. Démarrer spec 002 (notion_writer) en parallèle si VPN tjs KO demain
