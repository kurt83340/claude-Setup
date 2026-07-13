# Spec — 001 ERP Connector

**Statut :** Approved
**Date création :** 2026-05-23
**Owner :** Julien
**Tracking roadmap :** [ROADMAP.md Phase 1](../../../ROADMAP.md)

## Quoi

Module Python `sap_connector` qui encapsule les interactions avec SAP B1 Service Layer : authentification, fetch des commandes en incremental, fetch des lignes de commande, gestion retry/erreurs.

## Pourquoi

C'est le composant qui lit les données source. Sans lui, pas de sync possible. Doit être :

- **Robuste** : retry automatique, gestion 401, gestion 5xx
- **Testable** : 80%+ coverage, tests unitaires avec mocks
- **Réutilisable** : pourra être utilisé pour d'autres entités SAP en v2 (clients, articles)

## User stories couvertes

- **US1** En tant que workflow n8n, je veux récupérer les commandes créées/modifiées depuis un timestamp X
- **US2** En tant que workflow n8n, je veux récupérer les lignes détail d'une commande donnée
- **US3** En tant que workflow n8n, je veux que l'auth soit transparente (re-login auto si expiré)

## Critères d'acceptation

- [ ] `SapClient.get_orders_since(timestamp)` retourne `list[Order]` avec pagination transparente
- [ ] `SapClient.get_order_lines(doc_entry)` retourne `list[OrderLine]`
- [ ] Auth automatique : re-login si 401, sans intervention caller
- [ ] Retry 3x avec backoff exponentiel sur 5xx et timeout
- [ ] Logs structurés (structlog JSON) sur toutes les méthodes publiques
- [ ] Coverage tests >= 80%
- [ ] Tests d'intégration sur l'env staging ACME (VPN requis)
- [ ] Documentation des classes/méthodes (docstrings Google style)

## Out of scope

- Cache des résultats (pas nécessaire pour la cadence 10 min)
- Création/update de commandes (lecture seule v1)
- Autres entités SAP (clients, articles → v2)

## Dépendances

- ADR-0001 (stack) et ADR-0002 (auth) validés
- Accès SAP B1 Service Layer (voir ACCESS.md)
- VPN ACME opérationnel pour tests d'intégration

## Risques

- API SAP instable certains jours (Paul a confirmé) → mitigation via retry + alerting
- Schema SAP peut changer (rare mais possible) → tests d'intégration nous alerteront
