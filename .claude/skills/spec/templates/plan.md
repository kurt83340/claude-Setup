# Plan — {{SPEC_TITRE}}

> COMMENT on implémente la feature `{{SPEC_ID}}-{{SPEC_KEBAB}}`.

**Date :** {{SPEC_DATE}}

## Approche technique

{{Description de l'approche en 3-5 phrases. Pattern principal utilisé.}}

## Architecture

```
{{Diagramme ASCII inline ou ref vers diagrams/}}
```

## Modules / fichiers impactés

| Fichier     | Action                | Notes                    |
| ----------- | --------------------- | ------------------------ |
| `src/...`   | nouveau / modif / del | {{role}}                 |
| `tests/...` | nouveau               | tests unit + integration |

## Flux de données

1. {{Étape 1 : input → process → output}}
2. {{Étape 2}}
3. {{Étape 3}}

## Erreurs / cas limites

| Cas                    | Comportement attendu                   |
| ---------------------- | -------------------------------------- |
| {{Input invalide}}     | {{validation upstream, message clair}} |
| {{Service tiers down}} | {{retry 3x, fallback X, log Sentry}}   |
| {{Rate limit atteint}} | {{sleep + retry, alert si > 5 min}}    |

## ## Décisions (locales à cette feature)

> Décisions tech **locales** à cette spec uniquement. Si cross-feature → promouvoir en ADR via `/adr`.

### D1 — {{titre}}

**Choix :** {{option retenue}}
**Pourquoi :** {{1-2 phrases}}
**Alternatives écartées :** {{...}}

### D2 — {{titre}}

...

## Sécurité

- {{Authent / autoris}}
- {{Données sensibles : où / comment}}
- {{Logs : ne pas leak credentials/PII}}

## Performance

- {{Cibles : latence, throughput, memory}}
- {{Bottleneck connu}}

## Tests

- **Unit** : {{couverture cible, fichiers tests}}
- **Integration** : {{scénarios E2E principaux}}
- **Load** : {{si applicable}}

## Liens

- Spec : [spec.md](spec.md)
- Research : [research.md](research.md)
- Tasks : [tasks.md](tasks.md)
- ADRs liés : {{liste}}
