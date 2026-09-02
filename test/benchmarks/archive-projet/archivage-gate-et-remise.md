---
name: archivage-gate-et-remise
skill: archive-projet
input: /archive-projet "projet livré, mission terminée" — sur un projet template rempli, repo git propre, sans worktree, auto-memory présente
state: projet généré rempli minimal (HANDOFF/ROADMAP/CHANGELOG existants), repo git commité, ~/.claude/projects/<slug>/ présent dans le home de test
assert-contains:
  - "--dry-run"
  - "COMMANDE FINALE"
  - ".claude/archived"
assert-not-contains:
  - "Traceback"
  - "mv exécuté"
---

## Attendu

- Étape 1 (bilan) déroulée AVANT toute mécanique : HANDOFF final + ROADMAP gelée à l'état
  réel + entrée CHANGELOG « Archivage » — pas d'embellissement des statuts
- Le script est d'abord lancé en `--dry-run` et son rapport (destination, scan, référents
  externes, auto-memory) est montré à l'utilisateur — **gate** avant l'exécution réelle
- Après exécution réelle : bannière en tête de CLAUDE.md + `.claude/archived` **committés**
  (commit final) avant la remise de la commande
- La commande finale (`mkdir -p` + `mv` projet + `mv` auto-memory) est REMISE à l'utilisateur
  avec la consigne explicite « fermer cette session d'abord » — l'agent ne l'exécute JAMAIS
  lui-même depuis la session courante
- Les référents externes (crontab / CI / n8n) sont rapportés et expliqués, jamais « corrigés »
  silencieusement
