---
name: rapport-lecture-seule
skill: doc-health
input: /doc-health sur un projet dont le HANDOFF date de 10 jours et dont une spec est incohérente avec la ROADMAP
state: projet rempli minimal — HANDOFF.md vieilli à J-10 (touch -d), ROADMAP avec `[~] 001-x — **EN COURS**`, mais specs/001-x/spec.md porte `status: done` en frontmatter
assert-contains:
  - "🔴"
  - "status: done"
assert-not-contains:
  - "Traceback"
  - "command not found"
---

## Attendu

- HANDOFF > 7 jours → flaggé 🔴 avec l'action (`/handoff`)
- Incohérence `status: done` (frontmatter) vs `[~]` (ROADMAP) → flaggée 🟠 « resync »
- **Aucun fichier modifié** : `git status` identique avant/après (lecture seule stricte)
- Rapport final priorisé 🔴/🟠/🟢 (jamais une liste plate)
- Un check qui échoue n'interrompt pas le scan (les étapes suivantes tournent quand même)
