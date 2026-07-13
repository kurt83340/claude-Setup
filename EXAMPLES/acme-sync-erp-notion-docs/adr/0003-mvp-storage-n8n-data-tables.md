---
status: accepted
scope: mvp
phase: 2026-Q2
supersedes: null
---

# 0003 — Stockage delta dans n8n Data Tables (pas de BDD séparée)

**Statut :** Accepted
**Date :** 2026-05-23
**Décideur :** Julien (validé Paul ACME IT)

## Contexte

Le sync delta nécessite de mémoriser :

- Le timestamp du dernier sync réussi (pour filtrer SAP par `UpdateDate gt X`)
- Les IDs des commandes déjà synchronisées (pour éviter doublons)
- Le token de session SAP (pour le refresh lazy — voir [ADR-0002](0002-mvp-auth-session-token-sap.md))

Options : ajouter une BDD ? Utiliser un fichier ? Utiliser n8n Data Tables ?

## Options considérées

### Option A — PostgreSQL dédié

- Pro : robuste, ACID, requêtes SQL
- Contre : infra supplémentaire à provisionner ACME (Paul peu enclin), overkill pour 3 tables

### Option B — SQLite local au container n8n

- Pro : léger, pas d'infra
- Contre : non persisté si container redémarré, pas backup, fragile

### Option C — n8n Data Tables (feature native depuis v1.x)

- Pro : intégré, persisté, UI accessible à Paul pour debug, pas d'infra ext
- Contre : limité (pas de jointure complexe), max 10k rows par table (suffisant pour notre usage)

### Option D — Redis

- Pro : rapide, TTL natif
- Contre : pas persisté par défaut, infra supplémentaire

## Décision

**Option C : n8n Data Tables**

3 tables :

- `sync_state` : timestamp dernier sync, token SAP (singleton, 1 row)
- `synced_orders` : DocNum des commandes déjà sync (~10k rows max, rotation à 90j)
- `sync_errors` : log des erreurs récurrentes (pour analyse)

## Conséquences

- Zéro infra supplémentaire
- Debuggable depuis n8n UI par Paul
- Persisté avec le n8n on-prem (backup ACME existant couvre)
- Suffisant pour v1 (volume ACME stable)

* Si on dépasse 10k rows → revoir (rotation tous les 90j devrait suffire)
* Pas de requêtes complexes (pas besoin pour notre cas)
* Couplage à n8n (mais c'est OK, on est all-in n8n de toute façon)

## Quand reconsidérer

- Volume > 10k commandes actives → migrer vers PostgreSQL
- Besoin de requêtes analytiques complexes
- Multi-tenant (plusieurs entités ACME) → schéma plus riche

## Liens

- ../specs/001-erp-connector/spec.md
- ../specs/003-error-handler/spec.md
- docs/conception/ARCHITECTURE.md (section Stack)
- https://docs.n8n.io/data/data-tables/
