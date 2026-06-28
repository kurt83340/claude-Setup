# Architecture — Sync ERP→Notion v1.0

> 🛠️ **Pour qui** : Paul (IT ACME), Julien (dev), futurs devs qui reprennent le code
> 📋 **Ce fichier dit** : le **COMMENT technique** (composants, stack, modules, flux de données, sécurité, observabilité)
> ❌ **Ne contient PAS** : vision business, user stories, métriques produit → voir [PRD.md](PRD.md)

**Statut :** Validée Paul IT 2026-05-29
**Dernière MAJ :** 2026-05-29

## 1. Vue d'ensemble

### Composants techniques

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   SAP B1        │ ─────►  │   n8n workflow   │ ─────►  │   Notion DB      │
│ Service Layer   │  HTTPS  │  (on-premise)    │  HTTPS  │  "Commandes"     │
└─────────────────┘  (VPN)  └──────────────────┘         └──────────────────┘
                                      ↕
                            ┌──────────────────┐         ┌────────────┐
                            │ Python helpers   │         │  Sentry    │ (erreurs)
                            │ (transformations)│         └────────────┘
                            └──────────────────┘         ┌────────────┐
                                      ↕                  │ SMTP ACME  │ (alertes)
                            ┌──────────────────┐         └────────────┘
                            │ n8n Data Tables  │
                            │  (state + delta) │
                            └──────────────────┘
```

### Séquence d'un run sync (10 min)

```
[Cron 10min]
     │
     ├─► Lit last_sync_timestamp depuis n8n Data Tables
     │
     ├─► GET SAP /Orders?$filter=UpdateDate gt {ts}
     │       │
     │       ├─ Si 401 ──► POST /Login → token → Cache → Retry GET
     │       └─ Si 200 ──► reçoit orders[] (paginé)
     │
     ├─► POUR CHAQUE commande :
     │       │
     │       ├─► Python helper : transform(sap_order) → notion_payload
     │       ├─► Check si DocNum déjà sync (n8n Data Table "synced_orders")
     │       └─► Si NEW ou UPDATED :
     │              ├─► Notion API : PATCH/POST /pages (upsert)
     │              └─► Add DocNum au cache
     │
     ├─► Update last_sync_timestamp = now
     │
     └─► SI > 3 erreurs consécutives :
            ├─► Sentry capture_exception
            └─► Email alert Paul + Julien
```

### Légende des états de commande

| État      | Description                                        |
| --------- | -------------------------------------------------- |
| `NEW`     | Vue pour la 1ère fois, à créer dans Notion         |
| `UPDATED` | Déjà sync mais `UpdateDate` change → patch Notion  |
| `SYNCED`  | Déjà à jour, on skip                               |
| `ERROR`   | Erreur upsert Notion → log + retry au prochain run |

→ Pour la **vision business** (flow actuel ACME vs cible) : [../cadrage/diagrams/flow-business-acme.md](../cadrage/diagrams/flow-business-acme.md)

## 2. Stack technique (vue archi)

Stack résumé des choix **structurants** avec ADR liés.
→ **Inventaire complet** (libs Python, services tiers, LLM, deploy) : [../stack.md](../stack.md)

| Couche            | Choix                   | Justification                                   | ADR                                                |
| ----------------- | ----------------------- | ----------------------------------------------- | -------------------------------------------------- |
| Orchestration     | **n8n** (on-premise)    | Contrainte ACME (politique IT), workflow visuel | [0001](../adr/0001-mvp-stack-n8n-python.md)        |
| Helpers complexes | **Python 3.12**         | Transformations métier non triviales en n8n raw | -                                                  |
| Stockage delta    | **n8n Data Tables**     | Pas de BDD séparée pour v1 (KISS)               | [0003](../adr/0003-mvp-storage-n8n-data-tables.md) |
| Auth ERP          | Session token rotatif   | Standard SAP B1, géré dans le workflow          | [0002](../adr/0002-mvp-auth-session-token-sap.md)  |
| Auth Notion       | Integration token       | Standard Notion API                             | -                                                  |
| Logging           | n8n executions + Sentry | Sentry pour les erreurs critiques               | -                                                  |

## 3. Modules

### Module 1 — `sap_connector` (Python)

- Wrapper SAP B1 Service Layer (auth, session refresh, retry)
- Méthodes : `get_orders_since(timestamp)`, `get_order_lines(order_id)`
- Tests : `tests/unit/test_sap_connector.py`

### Module 2 — `notion_writer` (Python)

- Wrapper Notion API (rate limit, batching)
- Méthodes : `upsert_order(order)`, `get_existing_orders()`
- Tests : `tests/unit/test_notion_writer.py`

### Module 3 — `n8n workflow` (visual)

- Trigger : Schedule node (10 min)
- Steps : auth SAP → fetch deltas → transform (Python helpers) → upsert Notion → log
- Exporté : `workflows/sync-erp.json`
- Spec détaillée : [specs/001-erp-connector/](specs/001-erp-connector/)

## 4. Flux de données

1. **Trigger** : n8n Schedule (10 min)
2. **Fetch** : SAP B1 → `GET /Orders?$filter=UpdateDate gt 'X'` (où X = dernier sync)
3. **Transform** : Python helper map SAP fields → Notion properties
4. **Detect delta** : check si commande déjà dans n8n Data Table "synced_orders"
5. **Upsert** : Notion API → create ou update
6. **Update state** : insert timestamp dans Data Table
7. **Log** : success/failure dans n8n executions + Sentry si erreur

## 5. Mapping champs

| SAP B1 (Order)    | Notion (Commande)         | Transformation                 |
| ----------------- | ------------------------- | ------------------------------ |
| `DocNum`          | `Numéro commande` (titre) | str                            |
| `CardCode`        | `Client (code)` (text)    | str                            |
| `CardName`        | `Client (nom)` (text)     | str                            |
| `DocTotal`        | `Montant HT` (number)     | float                          |
| `DocDate`         | `Date commande` (date)    | ISO 8601                       |
| `DocumentLines[]` | `Lignes` (relation)       | sub-pages Notion (1 par ligne) |

## 6. Sécurité

- Credentials SAP/Notion stockés dans **n8n credentials** (chiffrés)
- Lecture seule sur SAP (compte API dédié, voir [../ACCESS.md](../ACCESS.md))
- Communication via VPN ACME uniquement (pas d'exposition internet)
- Logs : pas de données client en clair (anonymisation des `CardName` dans Sentry)

## 7. Observabilité

- **n8n executions** : historique 30 jours intégré
- **Sentry** : alerting erreurs critiques (DSN dans .env)
- **Email alerts** : Paul + Julien si > 3 erreurs consécutives en 1h (configuré dans n8n)

## 8. Évolutions prévues (v2+)

- Cache Redis si volume > 500 commandes/jour
- Multi-tenant si autres clients adoptent
- Sync inverse Notion → ERP (créer commande depuis Notion)
