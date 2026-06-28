# Tasks — {{SPEC_TITRE}}

> Checklist d'exécution pour `{{SPEC_ID}}-{{SPEC_KEBAB}}`. Coche au fur et à mesure.

**Date :** {{SPEC_DATE}}
**Status :** [ ] 0/N tasks → MAJ au fil de l'eau

## Phase 1 — {{nom phase, ex: Setup}}

- [ ] **T1.1** : {{description courte}}
  - DoD : {{critère de fin clair}}
- [ ] **T1.2** : {{...}}
  - DoD : {{...}}
- [ ] **T1.3** : {{...}}

## Phase 2 — {{nom phase, ex: Implémentation}}

- [ ] **T2.1** : {{...}}
  - DoD : {{...}}
- [ ] **T2.2** : {{...}}
  - DoD : {{...}}

## Phase 3 — Tests + livraison

- [ ] **T3.1** : tests unitaires verts (couverture >= {{X}}%)
- [ ] **T3.2** : tests d'intégration verts (scénario principal)
- [ ] **T3.3** : lint / type check OK
- [ ] **T3.4** : update .claude/docs/code-map.md si nouveaux modules
- [ ] **T3.5** : `/feature-done {{SPEC_ID}}-{{SPEC_KEBAB}}`

## Definition of Done (global)

La feature est livrée quand :

- [ ] Tous les critères d'acceptation de [spec.md](spec.md) cochés
- [ ] Tests verts (unit + integration)
- [ ] Pas de TODO ou `// FIXME` dans le code
- [ ] Pas de leak credentials/secrets
- [ ] Documentation à jour (code-map, plan.md décisions)
- [ ] ADRs créés pour les décisions structurantes
- [ ] Commit + tag git

## Blockers / questions

- {{Blocker actif 1 : besoin accès / décision client}}
- {{Question ouverte sur point technique X}}
