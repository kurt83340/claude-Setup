# Research — 001 ERP Connector

**Date :** 2026-05-23
**Statut :** Exploration terminée, spec validée

## Question initiale

Comment implémenter un client Python pour SAP B1 Service Layer qui soit robuste, testable, et qui gère les particularités de l'API (auth session, pagination, retry) ?

## Options de libs explorées

### Lib 1 — `b1sl` (SDK communautaire)

- ⭐ 47 GitHub, dernier commit 2022
- Pro : abstraction prête, type hints
- Contre : pas maintenu, bugs sur les filtres OData ($filter, $top)
- Test : tentative d'utilisation → KO sur notre cas (filtre UpdateDate)
- **❌ Abandonné**

### Lib 2 — `requests` (manuel)

- Pro : familier, stable, mature
- Contre : pas async, retry à coder
- **⚠️ Possible mais moyen**

### Lib 3 — `httpx` (manuel)

- Pro : sync + async, API similar à requests, transports retry built-in
- Contre : un peu moins de community examples pour SAP
- **✅ Choisi**

## Pattern de retry exploré

- `tenacity` : standard Python, decorators propres, backoff configurable
- Alternative : retry manuel → trop de boilerplate
- **Décision : tenacity** avec 3 tentatives, backoff exponentiel (1s, 2s, 4s)

## Pattern d'auth exploré

Voir [ADR-0002](../../../adr/0002-mvp-auth-session-token-sap.md) pour la décision finale (session token lazy refresh).

## Pagination

L'API SAP B1 limite à 20 résultats par défaut, paramétrable via `$top` (max 100).
Pour > 100 résultats : utiliser `@odata.nextLink` ou paginer manuellement avec `$skip`.

Test sur le volume ACME : 50 commandes/jour → 1 page suffit en mode incremental, mais en backfill (jusqu'à 30 jours) on peut avoir 1500+ commandes → pagination indispensable.

## Test mocking

Comparaison :

- `responses` : populaire mais ne supporte pas httpx
- `respx` : équivalent pour httpx, API similaire
- `pytest-httpx` : alternative, plus verbose
- **Choisi : `respx`** (intégration cleane avec httpx)

## Refs

- Doc SAP B1 Service Layer :  [cadrage/documents/2026-05-21-doc-sap-service-layer.pdf](../../../cadrage/documents/)
- httpx docs : https://www.python-httpx.org/
- tenacity docs : https://tenacity.readthedocs.io/
- respx docs : https://lundberg.github.io/respx/
