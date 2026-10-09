---
name: amend-partiel
skill: adr
input: /adr amend 0002 infra "Agents du jalon 2 sur le poste local (remplace « tout sur le cloud » pour ce seul point)"
state: ADR 0001 et 0002 acceptés dans adr/ (0002 décide « tout sur le cloud » et deux autres points), index adr/README.md à jour, CHANGELOG avec une section Decided
assert-contains:
  - "amends: 0002"
  - "Point remplacé"
  - "point amendé par"
assert-not-contains:
  - "status: superseded"
  - "{{"
---

## Attendu

- Un nouvel ADR 0003 est créé avec `amends: 0002` et `supersedes: null` ; sa Décision nomme le point remplacé
- L'ADR 0002 garde `status: accepted` et tout son corps : seul s'ajoute en tête un bandeau daté « Point remplacé » qui
  renvoie à 0003
- L'index `adr/README.md` garde 0002 dans sa table, au statut « Accepted (point amendé par 0003) », et ajoute 0003 dans
  sa table de scope
- Le CHANGELOG reçoit la décision dans `Decided`
