# Projet ACME — Sync ERP→Notion

Automatisation n8n + Python pour synchroniser les commandes SAP B1 → Notion DB ACME.

> ⚠️ **Exemple de référence** — montre à quoi ressemble un projet rempli. **Peut drifter** : non maintenu en lockstep avec le template (un check CI vérifie seulement la règle des 3 `@`-imports ci-dessous). Pour les conventions à jour, fie-toi au template, pas à cet exemple.

> 🧭 **Comment marche & vit ce template** (skills, structure, workflow, agent) → [.claude/CLAUDE.md](.claude/CLAUDE.md)

## Documentation projet

> 🪶 **Chargement just-in-time** : seuls les 3 docs d'état vivant ci-dessous sont auto-chargés (`@`) ; le reste = liens lus à la demande (mesuré : ~1,5k vs ~14,6k tokens si on charge tout).

### 🔄 Auto-chargés (`@` — état vivant)

- Reprise session : @.claude/docs/HANDOFF.md ⭐
- Roadmap : @.claude/docs/ROADMAP.md
- **Code map** : @.claude/docs/code-map.md ⭐ (règles de couplage + gotchas — à respecter avant d'éditer)

### 📂 Lus à la demande (liens — pas auto-chargés)

- 📥 **Cadrage** : [cadrage/README.md](.claude/docs/cadrage/README.md)
- 🎨 **Conception** : [research](.claude/docs/conception/research.md) · [PRD](.claude/docs/conception/PRD.md) · [ARCHITECTURE](.claude/docs/conception/ARCHITECTURE.md) · [tasks](.claude/docs/conception/tasks.md) · specs → `.claude/docs/specs/`
- 🔄 **Suivi** : [ACCESS](.claude/docs/ACCESS.md) · [CHANGELOG](.claude/docs/CHANGELOG.md) · [leçons](.claude/docs/lecons.md) · [stack](.claude/docs/stack.md)
- 📚 **Transversaux** : [ADR](.claude/docs/adr/) · [GLOSSARY](.claude/docs/GLOSSARY.md) · [RUNBOOK](.claude/docs/RUNBOOK.md)

## Skills projet (stack n8n)

- Plugin officiel **`n8n-mcp-skills`** (14 skills n8n + hooks — `/plugin marketplace add czlonkowski/n8n-skills`)
- `/deploy` (skill projet maison, push prod — `disable-model-invocation: true`)
- Skills cœur (`/handoff`, `/spec`, `/feature-done`, …) → inventaire dans [.claude/CLAUDE.md](.claude/CLAUDE.md)

## Reminders critiques

- Credentials **JAMAIS** dans le repo (stockage : `.claude/docs/ACCESS.md`)
- `.claude/docs/HANDOFF.md` à update **à chaque fin de session** (via `/handoff`)
- Décision tech structurante → créer un ADR (immuable : on ne modifie pas, on supersede)
