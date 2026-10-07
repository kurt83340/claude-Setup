---
name: consigner-avant
skill: handoff
input: /handoff en fin de session où l'utilisateur a décidé un plafond de dépense cloud, ouvert un accès (API activée, conditions acceptées) et payé un piège, sans ADR, ni ACCESS.md, ni leçon
state: HANDOFF déjà rempli (format standard, ≤ 40 lignes) ; ADR, ACCESS.md et lecons.md sans trace de la session
assert-contains:
  - "Consigné ailleurs"
  - "/adr"
  - "ACCESS.md"
assert-not-contains:
  - "{{"
---

## Attendu

- Avant de composer le HANDOFF (Étape 3), le skill liste les éléments durables de la session et leur
  place versionnée : le plafond → ADR (`/adr`), l'accès → `ACCESS.md`, le piège → `/lecon`
- Il propose de les consigner **avant** la réécriture, jamais après
- Le diff présenté (Étape 4) dit pour chaque élément où il est consigné : aucune information de la
  session ne vit seulement dans le nouveau HANDOFF
