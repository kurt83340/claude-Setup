# Spec — 002 Notion Writer

**Statut :** Approved
**Date création :** 2026-05-23
**Owner :** Julien
**Tracking roadmap :** [ROADMAP.md Phase 1](../../../ROADMAP.md)

## Quoi

Module Python `notion_writer` qui encapsule l'écriture dans Notion DB "Commandes" : upsert par DocNum, gestion rate limit, mapping champs SAP → properties Notion.

## Pourquoi

Pendant 001 lit l'ERP, 002 écrit dans Notion. Composants séparés = testables indépendamment, réutilisables pour d'autres DBs Notion en v2.

## Critères d'acceptation

- [ ] `NotionWriter.upsert_order(order: Order) → str` retourne l'ID de la page Notion créée/updated
- [ ] Détection automatique create vs update (par DocNum)
- [ ] Rate limit géré : pas plus de 3 req/sec
- [ ] Retry 3x sur 429 avec backoff
- [ ] Schema validation au démarrage (check que DB Notion a bien les properties attendues)
- [ ] Tests unitaires (mock httpx) coverage >= 80%
- [ ] Test d'intégration sur DB Notion staging

## Out of scope

- Création/modification des DBs Notion (Marie gère)
- Sub-pages pour les lignes (différé en v1.1)
- Recherche avancée dans Notion

## Data model

Voir [data-model.md](data-model.md)

## Dépendances

- Spec 001 livrée (utilise `Order` from `sap_connector.models`)
- Accès Notion integration token (voir ACCESS.md)
- DB "Commandes" partagée avec l'integration par Marie

## Risques

- Notion change le schema de la DB → mitigation : validation au démarrage
- Rate limit plus restrictif sur tenants gros volumes → mitigation : sleep 350ms entre req
