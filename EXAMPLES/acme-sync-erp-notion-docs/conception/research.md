# Research — Conception macro projet

> Brainstorm initial + exploration d'options + capture des pivots ultérieurs.
> Au niveau **projet entier** (pas au niveau d'une feature — celui-là vit dans `../specs/00X-feature/research.md`).

## 2026-05-22 — Brainstorm initial

### Question de départ

Comment automatiser le flow "commande SAP → Notion DB" pour ACME, en respectant leurs contraintes (n8n on-premise obligatoire, lecture seule, < 15 min latence) ?

### Options explorées

#### Option 1 — Sync direct SAP → Notion via Python pur (sans n8n)

- **Pour** : full control, pas de dépendance n8n
- **Contre** : pas d'UI monitoring, faut coder scheduling/retry/alerting, dette technique long terme pour Paul
- **Effort** : 4-5 semaines
- **Décision** : ❌ rejeté

#### Option 2 — n8n cloud + helpers Python

- **Pour** : UI monitoring nickel, retry built-in, time-to-market rapide
- **Contre** : contrainte ACME interdit le SaaS pour données métier
- **Décision** : ❌ rejeté (contrainte client)

#### Option 3 — n8n on-premise + helpers Python ⭐

- **Pour** : respecte contrainte ACME, monitoring intégré, retry/scheduling natif, Paul peut maintenir
- **Contre** : Paul doit apprendre n8n (estimation 1 semaine)
- **Effort** : 2-3 semaines
- **Décision** : ✅ retenu — voir [ADR-0001](../adr/0001-mvp-stack-n8n-python.md)

#### Option 4 — Apache Airflow

- **Pour** : robuste, scalable
- **Contre** : overkill pour 1 workflow, gros à déployer
- **Décision** : ❌ rejeté (overengineering)

### Questions ouvertes initiales (à clarifier au kickoff)

- ✅ Sync inverse (Notion → SAP) attendu ? → **NON pour v1** (Marie kickoff 20/05)
- ✅ Notifications Slack ? → **NON pour v1**, peut-être v2 ([idees/2026-05-23-slack-alerts.md](../idees/2026-05-23-slack-alerts.md))
- ✅ Multi-tenant futur ? → pas pertinent maintenant
- ✅ Volume réel ? → ~50 commandes/jour, pics 200 fin de mois

### Hypothèses retenues pour le PRD

- API SAP B1 stable en prod (Paul a confirmé, mais à challenger avec retry/alerting)
- Notion DB schema ne change pas pendant le projet (validation au démarrage)
- VPN ACME up 99% du temps (retry + buffer)

### Décisions issues du brainstorm

1. Stack n8n on-prem + Python → ADR-0001
2. Auth SAP session token rotatif → ADR-0002
3. Stockage delta dans n8n Data Tables → ADR-0003
4. Pas de cache Redis pour v1 (over-engineering)

---

## Template pour pivots ultérieurs

Si la hiérarchie demande un pivot, append ici une section datée :

```markdown
## YYYY-MM-DD — Pivot [titre]

### Contexte du pivot

Pourquoi on doit changer (réunion, mail, ticket → voir cadrage/reunions/)

### Nouvelles options explorées

- Option A : ...
- Option B : ...

### Décision retenue

- ...

### Conséquences

- PRD bumpé v1.0 → v2.0
- ROADMAP refondu (voir ../ROADMAP.md section v2)
- ADR-00XX créé si pivot tech
```
