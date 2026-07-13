---
name: fresh-regen
skill: handoff
input: /handoff en fin de première session de travail (2-3 fichiers modifiés, tests verts)
state: projet fraîchement initialisé — .claude/docs/HANDOFF.md contient encore > 5 placeholders {{...}} (état post-init), quelques commits récents
assert-contains:
  - "## Continuation State"
  - "Commande de reprise:"
  - "## Journal"
assert-not-contains:
  - "{{"
---

## Attendu

- Détection « fresh » (> 5 placeholders) → HANDOFF regénéré from scratch, aucune section
  fantôme « préservée » depuis le template
- Bloc **Continuation State** présent avec les 5 clés (`Spec` / `Task` / `Fichiers en cours` /
  `Bloqué sur` / `Commande de reprise`), même valorisées à `aucune`
- Le **diff est présenté AVANT écriture** (jamais de Write direct sans confirmation)
- **Journal** : exactement 1 ligne appendée pour cette session — jamais de réécriture
- Aucun placeholder `{{...}}` résiduel dans le fichier écrit
