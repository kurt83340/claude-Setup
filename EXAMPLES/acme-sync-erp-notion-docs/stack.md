# Stack — Sync ERP→Notion (ACME)

> **Inventaire technique pur** : langage, libs, services tiers, LLM, deploy, monitoring.
> Le **POURQUOI** des choix tech vit dans [adr/](adr/). L'**ARCHI** globale dans [conception/ARCHITECTURE.md](conception/ARCHITECTURE.md).
> Ce fichier = **vue catalogue rapide** pour répondre à "quelles techs on utilise et pour quoi ?".

**Dernière MAJ :** 2026-05-29 (Julien)

## Langage(s) & runtime

| Item   | Version          | Notes                  |
| ------ | ---------------- | ---------------------- |
| Python | 3.12.x (CPython) | uv pour env management |
| n8n    | 1.x on-premise   | hébergement ACME       |

## Orchestration

| Composant       | Choix                      | Voir                                         |
| --------------- | -------------------------- | -------------------------------------------- |
| Workflow engine | **n8n** on-premise         | [ADR-0001](adr/0001-mvp-stack-n8n-python.md) |
| Helpers métier  | Python (modules séparés)   | [code-map.md](code-map.md)                   |
| Scheduling      | n8n Schedule node (10 min) | —                                            |

## Stockage & data

| Source/Destination       | Usage                     | Voir                                                              |
| ------------------------ | ------------------------- | ----------------------------------------------------------------- |
| **SAP B1 Service Layer** | Lecture seule (commandes) | [ADR-0002](adr/0002-mvp-auth-session-token-sap.md)                |
| **Notion API**           | Écriture DB "Commandes"   | [data-model.md](conception/specs/002-notion-writer/data-model.md) |
| **n8n Data Tables**      | State delta + token cache | [ADR-0003](adr/0003-mvp-storage-n8n-data-tables.md)               |

→ **Pas de BDD séparée** pour v1 (KISS — n8n Data Tables suffit).

## Librairies Python (rôles)

| Lib             | Version | Pour quoi                      | Module qui l'utilise                         |
| --------------- | ------- | ------------------------------ | -------------------------------------------- |
| `httpx`         | ^0.27   | Client HTTP async-ready        | `sap_connector`, `notion_writer`             |
| `tenacity`      | ^9      | Retry exponentiel (3x backoff) | `sap_connector._http`, `notion_writer._http` |
| `pydantic`      | ^2.7    | Validation modèles             | `sap_connector.models`                       |
| `structlog`     | ^24     | Logs JSON structurés           | tous modules                                 |
| `sentry-sdk`    | ^2      | Error tracking                 | `error_handler.notifier`                     |
| `notion-client` | ^2      | Wrapper Notion API officiel    | `notion_writer`                              |
| `respx`         | ^0.21   | Mocks httpx (tests)            | `tests/unit/`                                |
| `pytest`        | ^8      | Framework tests                | `tests/`                                     |
| `pytest-cov`    | ^5      | Coverage reports               | `tests/`                                     |
| `ruff`          | ^0.7    | Linter + formatter             | dev tool                                     |
| `mypy`          | ^1.10   | Type checker (strict)          | dev tool                                     |
| `pre-commit`    | ^3      | Hooks pré-commit               | dev tool                                     |

## LLM providers (par feature)

| Feature                     | LLM utilisé | Coût estimé | Notes                           |
| --------------------------- | ----------- | ----------- | ------------------------------- |
| _(aucun usage LLM pour v1)_ | —           | —           | Sync pur, pas d'AI dans le flow |

⚠️ **Si une feature future utilise un LLM** (ex: catégorisation auto commandes, résumé automatique), documenter ici **ET** dans `specs/00X-feature/plan.md` (section "LLM choisi + raison + coût estimé").

Possibles options à considérer plus tard :

- Claude Sonnet 4.6 / 4.7 (raisonnement)
- Claude Haiku 4.5 (rapide, peu coûteux)
- GPT-4o / GPT-5 (si client préfère OpenAI)

## Services tiers / SaaS

| Service                    | Usage                       | Statut                                    | Coût                | Voir                                                                                       |
| -------------------------- | --------------------------- | ----------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------ |
| **Sentry**                 | Error tracking              | Compte perso (v1), migration ACME en v1.1 | Free tier           | [reunions/2026-05-23-validation-archi.md](cadrage/reunions/2026-05-23-validation-archi.md) |
| **1Password vault "ACME"** | Stockage credentials maître | Actif (partagé Marie)                     | Inclus contrat ACME | [ACCESS.md](ACCESS.md)                                                                     |
| **SMTP ACME**              | Email alerts ops            | ⏳ Ticket IT #4527                        | Inclus              | [RUNBOOK.md](RUNBOOK.md)                                                                   |

❌ **Pas utilisé** : Doppler, AWS Secrets Manager, Datadog, Grafana Cloud, Slack API.

## Infra & Deploy

| Item                       | Choix                       | Notes                                            |
| -------------------------- | --------------------------- | ------------------------------------------------ |
| Hébergement n8n            | On-premise ACME             | Politique IT                                     |
| Hébergement Python helpers | Même infra (containers n8n) | —                                                |
| VPN                        | ACME (compte `julien.ext`)  | Voir [ACCESS.md](ACCESS.md)                      |
| CI/CD                      | GitHub Actions              | lint + tests sur PR                              |
| Versioning                 | Tags git `vYYYY.MM.DD-HHMM` | Voir [git-workflow.md](../rules/git-workflow.md) |

## Auth & Sécurité

| Auth            | Pattern                                                      | Voir                                               |
| --------------- | ------------------------------------------------------------ | -------------------------------------------------- |
| SAP B1          | Session token rotatif (lazy refresh)                         | [ADR-0002](adr/0002-mvp-auth-session-token-sap.md) |
| Notion          | Integration token (créé par Marie)                           | [ACCESS.md](ACCESS.md)                             |
| Secrets storage | `.env` local + n8n credentials (AES-256) + 1Password partagé | [ACCESS.md](ACCESS.md)                             |

❌ **Anti-patterns interdits** :

- Credentials dans le code source
- Credentials dans les logs (anonymisation Sentry)
- Compte API SAP en écriture (lecture seule uniquement)

## Tests

| Type        | Framework                         | Couverture        | Lancement                   |
| ----------- | --------------------------------- | ----------------- | --------------------------- |
| Unit        | `pytest` + `respx`                | >= 80% (objectif) | `pytest tests/unit/`        |
| Integration | `pytest` + testcontainers (futur) | sur staging       | `pytest tests/integration/` |
| E2E         | run manuel du workflow n8n        | smoke tests       | manuel ou scripts/deploy.py |

Voir [testing.md](../rules/testing.md) pour conventions.

## Monitoring & Observability

| Source             | Quoi                            | Retention             |
| ------------------ | ------------------------------- | --------------------- |
| **n8n executions** | Historique runs (success/fail)  | 30 jours              |
| **Sentry**         | Erreurs critiques (FATAL)       | Free tier limite      |
| **Email alerts**   | Si > 3 erreurs consécutives/h   | Live                  |
| **Logs Python**    | `structlog` JSON sur stdout n8n | N/A (capturé par n8n) |

❌ **Pas de** : APM, traces distribuées, dashboard custom (n8n suffit pour v1).

## Évolutions stack prévues (v2+)

- **Cache Redis** si volume > 500 commandes/jour
- **PostgreSQL** si on dépasse capacités n8n Data Tables
- **Migration Sentry** sur compte ACME (planifié v1.1)
- **Dashboard Grafana** sur métriques n8n (spec 004)

## Mise à jour

- **Nouvelle lib ajoutée** : update la table "Librairies Python"
- **Nouveau service SaaS** : update "Services tiers"
- **Feature ajoute usage LLM** : update "LLM providers" + référencer dans specs/00X/plan.md
- **Changement infra** : update "Infra & Deploy"
- **Source of truth** : `pyproject.toml` pour les libs Python exactes (versions), CE fichier pour le contexte humain (WHY + services tiers + LLM)
