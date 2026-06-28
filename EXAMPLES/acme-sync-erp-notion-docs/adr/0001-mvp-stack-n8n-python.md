---
status: accepted
scope: mvp
phase: 2026-Q2
supersedes: null
---

# 0001 — Stack : n8n on-prem + Python helpers

**Statut :** Accepted
**Date :** 2026-05-23
**Décideur :** Julien (validé Paul ACME IT)

## Contexte

Le projet ACME nécessite une orchestration de workflow (trigger schedule, fetch API SAP, transform, push Notion, gestion erreurs). Plusieurs stacks possibles.

Contraintes ACME :

- Pas de SaaS pour données métier (politique IT) → exit n8n Cloud, Make, Zapier
- Doit tourner on-premise sur leur infra
- Paul a déjà du Python en production → familier de l'équipe
- Budget limité, pas de gros dev framework

## Options considérées

### Option A — Pur Python (FastAPI worker + cron)

- Pro : full control, pas de dépendance externe
- Contre : tout à coder (UI monitoring, retry, scheduling, alerting)
- Effort : 4-5 semaines

### Option B — n8n on-premise + Python helpers

- Pro : workflow visuel, monitoring intégré, retry built-in, scheduling intégré
- Contre : dépendance à n8n, courbe d'apprentissage Paul
- Effort : 2-3 semaines

### Option C — Apache Airflow on-premise

- Pro : robuste, scalable, large communauté
- Contre : overkill pour 1 workflow, gros à déployer, Python-only
- Effort : 3-4 semaines

## Décision

**Option B : n8n on-prem + Python helpers**

n8n pour l'orchestration (auth, schedule, retry, UI monitoring), Python pour les transformations métier complexes (mapping SAP → Notion non trivial).

## Conséquences

- Time-to-market rapide (2-3 semaines au lieu de 4-5)
- Paul peut faire des modifs mineures sans coder (drag-drop n8n)
- Monitoring intégré (executions n8n)
- Retry, error handling, scheduling : built-in

* Dépendance à n8n (mais c'est OSS, on peut self-host)
* Courbe d'apprentissage initial pour Paul sur n8n
* Helpers Python = un peu de code à maintenir quand même

## Liens

- ../conception/specs/001-erp-connector/spec.md
- docs/conception/ARCHITECTURE.md (section Stack)
- https://docs.n8n.io/
