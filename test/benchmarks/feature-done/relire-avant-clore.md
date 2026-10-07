---
name: relire-avant-clore
skill: feature-done
input: /feature-done 001-socle quand tous les tasks sont cochés et que l'epic du jalon, dans l'outil de tickets, porte encore une question qu'un ticket enfant a résolue
state: spec 001 complète (tasks [x], DoD rempli) ; l'epic décrit « limite de l'instance : inconnue », alors qu'un ticket enfant a relevé la limite
assert-contains:
  - "epic"
  - "question"
assert-not-contains:
  - "{{"
---

## Attendu

- Étape 1 : avant de proposer la clôture, le skill relit l'epic du jalon (critères, questions, risques)
- La question résolue par le ticket enfant est signalée, et sa réponse reportée dans l'epic avant de le
  clore ; aucun critère ne reste sans résultat
- La clôture n'est proposée qu'après cette relecture
