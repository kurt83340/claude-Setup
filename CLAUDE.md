# {{PROJECT_NAME}}

{{1-2 phrases qui résument le projet : "Automatisation X pour Y" / "App de gestion Z" / etc.}}

> 🧭 **Comment marche & vit ce template** (skills, structure, workflow, agent) → [.claude/CLAUDE.md](.claude/CLAUDE.md)

## Documentation projet

> 🪶 **Chargement just-in-time** : seuls les 3 docs d'état vivant ci-dessous sont auto-chargés (`@`) à chaque session ; le reste = **liens simples** que Claude lit **à la demande**. Tout charger en `@` coûte ~10× plus de contexte au démarrage (mesuré : ~14,6k vs ~1,5k tokens sur un projet rempli) et dégrade la qualité quand le contexte gonfle ([context engineering, Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). **Garde la liste auto-chargée courte.**

### 🔄 Auto-chargés (`@` — état vivant, toujours en contexte)

- Reprise session : @.claude/docs/HANDOFF.md ⭐
- Roadmap : @.claude/docs/ROADMAP.md
- **Code map** : @.claude/docs/code-map.md ⭐ (règles de couplage + gotchas non-déductibles — à respecter avant d'éditer)

### 📂 Lus à la demande (liens — pas auto-chargés)

- 📥 **Cadrage** : [cadrage/README.md](.claude/docs/cadrage/README.md)
- 🎨 **Conception** : [research](.claude/docs/conception/research.md) · [PRD](.claude/docs/conception/PRD.md) · [ARCHITECTURE](.claude/docs/conception/ARCHITECTURE.md) · [tasks (plan MVP)](.claude/docs/conception/tasks.md) · specs → `.claude/docs/specs/00X-feature/`
- 🔄 **Suivi** : [ACCESS](.claude/docs/ACCESS.md) · [CHANGELOG](.claude/docs/CHANGELOG.md) · [leçons](.claude/docs/lecons.md) · [stack](.claude/docs/stack.md)
- 📚 **Transversaux** : [ADR](.claude/docs/adr/) · [GLOSSARY](.claude/docs/GLOSSARY.md) · [RUNBOOK](.claude/docs/RUNBOOK.md)

## Conventions techniques

> Les règles dans `.claude/rules/*.md` sont **déjà auto-chargées** par Claude Code — pas besoin de `@-import` ici (ce serait du double chargement). Idéalement, scope-les par chemin (frontmatter `paths:`) pour qu'elles ne chargent que sur les fichiers concernés.

- [code-style](.claude/rules/code-style.md) · [testing](.claude/rules/testing.md) · [git-workflow](.claude/rules/git-workflow.md) · [doc-lookup](.claude/rules/doc-lookup.md)

## Reminders critiques

- Credentials **JAMAIS** dans le repo (stockage : `.claude/docs/ACCESS.md`)
- `.claude/docs/HANDOFF.md` à update **à chaque fin de session** (via `/handoff`)
- Décision tech structurante → créer un ADR (via `/adr`)
- ADR **immuable** : on ne modifie jamais, on crée un nouveau qui supersede

---

> ℹ️ **Tous les placeholders ne sont pas obligatoires** — adapte selon ton projet (script jetable = 30%, projet client = 70-80%, enterprise = 100%). Supprime les sections non pertinentes.
