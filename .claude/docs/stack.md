# Stack — {{PROJECT_NAME}}

> **Inventaire technique pur** : langage, libs, services tiers, LLM, deploy, monitoring.
> Le **POURQUOI** des choix tech vit dans [adr/](adr/). L'**ARCHI** globale dans [conception/ARCHITECTURE.md](conception/ARCHITECTURE.md).
> Ce fichier = **vue catalogue rapide** pour répondre à "quelles techs on utilise et pour quoi ?".

**Dernière MAJ :** {{YYYY-MM-DD}}

## Langage(s) & runtime

| Item                   | Version   | Notes           |
| ---------------------- | --------- | --------------- |
| {{Python / Node / Go}} | {{X.Y.Z}} | {{env manager}} |
| {{Autre runtime}}      | ...       | ...             |

## Orchestration

| Composant           | Choix          | Voir                     |
| ------------------- | -------------- | ------------------------ |
| {{Workflow engine}} | **{{techno}}** | [{{ADR-XXXX}}]({{path}}) |
| {{Scheduling}}      | ...            | —                        |

## Stockage & data

| Source/Destination | Usage                          | Voir                |
| ------------------ | ------------------------------ | ------------------- |
| **{{System 1}}**   | {{lecture / écriture / cache}} | [{{ADR}}]({{path}}) |
| **{{System 2}}**   | ...                            | ...                 |

## Librairies (rôles)

| Lib         | Version | Pour quoi | Module qui l'utilise |
| ----------- | ------- | --------- | -------------------- |
| `{{lib_1}}` | ^{{X}}  | {{usage}} | {{module}}           |
| `{{lib_2}}` | ^{{X}}  | ...       | ...                  |
| ...         | ...     | ...       | ...                  |

## LLM providers (par feature)

| Feature                            | LLM utilisé | Coût estimé | Notes              |
| ---------------------------------- | ----------- | ----------- | ------------------ |
| _(aucun usage LLM pour l'instant)_ | —           | —           | {{type de projet}} |

⚠️ **Si une feature utilise un LLM**, documenter ici **ET** dans `specs/00X-feature/plan.md` (section "LLM choisi + raison + coût estimé").

Options à considérer si besoin :

- Claude Sonnet 4.6 / 4.7 (raisonnement)
- Claude Haiku 4.5 (rapide, peu coûteux)
- GPT-4o / GPT-5 (si client préfère OpenAI)

## Services tiers / SaaS

| Service                   | Usage                | Statut                       | Coût               | Voir                   |
| ------------------------- | -------------------- | ---------------------------- | ------------------ | ---------------------- |
| **{{Sentry / autre}}**    | {{error tracking}}   | {{✅ actif / ⏳ en attente}} | {{free / X€/mois}} | [{{lien}}]({{path}})   |
| **{{Vault credentials}}** | {{stockage secrets}} | {{actif}}                    | {{inclus}}         | [ACCESS.md](ACCESS.md) |
| ...                       | ...                  | ...                          | ...                | ...                    |

❌ **Pas utilisé** : {{liste des services explicitement écartés}}.

## Infra & Deploy

| Item        | Choix                                 | Notes                                            |
| ----------- | ------------------------------------- | ------------------------------------------------ |
| Hébergement | {{cloud / on-prem / spécifique}}      | {{contrainte}}                                   |
| CI/CD       | {{GitHub Actions / GitLab CI / etc.}} | {{lint + tests sur PR}}                          |
| Versioning  | Tags git `vYYYY.MM.DD-HHMM`           | Voir [git-workflow.md](../rules/git-workflow.md) |

## Auth & Sécurité

| Auth            | Pattern                          | Voir                   |
| --------------- | -------------------------------- | ---------------------- |
| {{Système 1}}   | {{JWT / session / OAuth / etc.}} | [{{ADR}}]({{path}})    |
| Secrets storage | `.env` + {{vault}}               | [ACCESS.md](ACCESS.md) |

❌ **Anti-patterns interdits** :

- Credentials dans le code source
- Credentials dans les logs
- {{Autre anti-pattern spécifique projet}}

## Tests

| Type        | Framework                  | Couverture           | Lancement       |
| ----------- | -------------------------- | -------------------- | --------------- |
| Unit        | {{pytest / jest / vitest}} | >= {{X}}% (objectif) | `{{commande}}`  |
| Integration | {{...}}                    | {{...}}              | `{{commande}}`  |
| E2E         | {{...}}                    | {{smoke}}            | {{manuel / CI}} |

Voir [testing.md](../rules/testing.md) pour conventions.

## Monitoring & Observability

| Source             | Quoi                        | Retention   |
| ------------------ | --------------------------- | ----------- |
| {{Source 1}}       | {{logs / metrics / traces}} | {{X jours}} |
| {{Sentry / autre}} | {{erreurs}}                 | {{...}}     |

## Évolutions stack prévues (v2+)

- {{Si volume X → ajouter Y}}
- {{Migration prévue}}
- {{Refacto attendu}}

## Mise à jour

- **Nouvelle lib ajoutée** : update la table "Librairies"
- **Nouveau service SaaS** : update "Services tiers"
- **Feature ajoute usage LLM** : update "LLM providers" + référencer dans specs/00X/plan.md
- **Changement infra** : update "Infra & Deploy"
- **Source of truth** : `{{pyproject.toml | package.json}}` pour les libs exactes (versions), CE fichier pour le contexte humain (WHY + services tiers + LLM)
