# Research — 002 Notion Writer

**Date :** 2026-05-23
**Statut :** Spec validée

## Question

Comment écrire dans Notion DB de manière fiable, avec gestion du rate limit (3 req/sec) et idempotence (pas de doublons) ?

## Options libs

### `notion-client` (officielle JS port en Python)

- ⭐ 1.8k GitHub, maintenu
- Pro : standard, type hints, communauté
- Contre : sync uniquement (mais OK pour notre cas)
- **✅ Choisi**

### `notion-sdk-py`

- Plus communautaire, moins maintenu
- ❌ Non

## Rate limiting

Notion limite à **3 requêtes/seconde** par integration. Au-delà → 429.

Stratégies envisagées :

- Sleep manuel entre requêtes → simple mais bloquant
- `aiometer` (asyncio + rate limit) → async, overkill pour 50 commandes
- `tenacity` retry sur 429 → fail-safe mais pas optimal
- **Choisi : sleep manuel 350ms entre requêtes + tenacity sur 429** (ceinture + bretelles)

## Idempotence (pas de doublons)

Approche : utiliser `DocNum` SAP comme clé unique dans Notion.

- Au push : query Notion `filter by DocNum` → si existe, PATCH ; sinon CREATE
- Cache local (n8n Data Table `synced_orders`) pour éviter le query Notion à chaque fois

## Refs

- Notion API docs : https://developers.notion.com/reference
- Rate limit doc : https://developers.notion.com/reference/request-limits
- notion-client : https://github.com/ramnes/notion-sdk-py
