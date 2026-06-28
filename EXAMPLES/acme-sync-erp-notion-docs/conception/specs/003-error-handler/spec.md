# Spec — 003 Error Handler

**Statut :** Approved
**Date création :** 2026-05-23
**Owner :** Julien

## Quoi

Module de gestion centralisée des erreurs du workflow sync : capture, classification, retry, alerting, dégradation gracieuse.

## Pourquoi

Sans ça, une erreur transitoire (timeout VPN, 429 Notion, 5xx SAP) casserait tout le sync. On veut :

- Retry intelligent sur les erreurs transitoires
- Alerting humain sur les erreurs persistantes
- Visibilité (Sentry + n8n executions)

## Critères d'acceptation

- [ ] Classification erreurs : `RETRYABLE` vs `FATAL` vs `IGNORABLE`
- [ ] Capture Sentry sur toutes les `FATAL`
- [ ] Email alert si > 3 erreurs consécutives en 1h (configurable)
- [ ] Pas d'alerte spam (cooldown 30 min entre alertes identiques)
- [ ] Log structuré JSON sur chaque erreur (catégorie + contexte)
- [ ] Métriques exposées : count par catégorie, last_error_at

## Catégories d'erreurs

| Catégorie     | Exemples                                                | Action                      |
| ------------- | ------------------------------------------------------- | --------------------------- |
| **RETRYABLE** | Timeout, 5xx SAP, 429 Notion, VPN flaky                 | Retry tenacity (3x backoff) |
| **FATAL**     | 401 persistant, schema Notion KO, credentials manquants | Stop workflow + alert       |
| **IGNORABLE** | Order avec data invalide isolée                         | Skip + log warning          |

## Out of scope

- Dashboard custom (n8n executions + Sentry suffisent pour v1)
- Auto-healing (revenir d'une erreur sans intervention) → trop ambitieux v1

## Dépendances

- Sentry DSN dans `.env`
- SMTP ACME pour alertes email (en attente, voir ACCESS.md)
