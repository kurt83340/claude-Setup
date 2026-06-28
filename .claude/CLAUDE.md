# {{PROJECT_NAME}} — Template, skills & agent

> Ce fichier décrit **comment le template est structuré et comment il vit** : skills, agent, workflow doc.
> Le [`CLAUDE.md` racine](../CLAUDE.md) décrit le **projet** (résumé, navigation doc, conventions).
> Les deux sont chargés automatiquement par Claude Code à chaque session (cwd = racine + remontée d'arborescence).

## 🧭 Comment vivre avec ce template

**Lis EN PREMIER** : @rules/template-maintenance.md
→ explique la structure, le workflow fin/début de session, quel skill/agent invoquer.

**Guide d'usage pratique** : [USAGE.md](../USAGE.md) (workflows quotidiens, skills, hooks, pivot, ADR, leçons).
**Convention complète** : [STRUCTURE.md](../STRUCTURE.md) (arborescence, naming, patterns 2026).

## Skills (`.claude/skills/`)

> Skills à plat dans `.claude/skills/<nom>/SKILL.md` (1 niveau — Claude Code ne scanne pas récursivement, cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192)). Invocation = `/<nom>` (le `name:` du frontmatter).

### Session & feature

- `/handoff` ⭐ — snapshot HANDOFF.md fin de session
- `/spec "<titre>"` ⭐ — scaffold nouvelle feature (4 fichiers + ROADMAP)
- `/feature-done <spec-id>` ⭐ — livraison feature
- `/pivot "<raison>"` — orchestrer un pivot client (9 étapes)

### Cycle de vie des artefacts (capture/promote/discard/archive)

- `/lecon [mode] <args>` — leçons : `<scope> "<titre>"` | `promote <date>` | `discard <date>` | `archive`
- `/adr [mode] <args>` — ADRs : `<scope> "<titre>"` | `supersede <NN>` | `deprecate <NN>` | `list`
- `/idee [mode] <args>` — idées : `"<titre>"` | `promote <date>` | `discard <date>` | `archive`

### Audit & technique

- `/doc-health` — audit hebdo de la doc
- `/codemap` — régénère `code-map.md` depuis `src/`

### Bootstrap

- `/init-from-template` — initialise un projet depuis ce template (UNE FOIS)

> 🗂️ **Inventaire canonique** : cette liste (**10 skills cœur**) est la **source de vérité** des skills du template. `README.md`, `USAGE.md` et `.claude/rules/template-maintenance.md` y **renvoient** — ne pas redupliquer ailleurs. Un check CI vérifie que chaque dossier `.claude/skills/*` y figure.

### Skills hors-template (stack-spécifiques — copiés à la demande depuis `EXAMPLES/skills-*`)

Hors du cœur (outillage non générique). `/init-from-template` les copie dans `.claude/skills/` selon le **type de projet** choisi :

- **n8n** (type `automation-n8n`) → `/n8n-push`, `/n8n-seed-db`, `/n8n-deploy` (source : [`EXAMPLES/skills-n8n/`](../EXAMPLES/skills-n8n/))
- **BDD / Alembic** (type `bdd-migration`) → `/db-migration` (source : [`EXAMPLES/skills-db/`](../EXAMPLES/skills-db/))

Quand un projet ajoute d'autres skills liés à sa stack, les installer dans `.claude/skills/` **et les recenser ici** : ce fichier reste l'inventaire unique de **tous** les skills — cœur ou stack.

## Slash commands projet

> Les « custom commands » (`.claude/commands/`) ont **fusionné avec les skills** — le template
> n'utilise plus que le format skill ([doc officielle](https://code.claude.com/docs/en/skills) :
> "Skills are recommended"). Pour ajouter un `/nom` projet : `.claude/skills/<nom>/SKILL.md`
> (exemples stack : [EXAMPLES/skills-n8n/](../EXAMPLES/skills-n8n/)).

## Agent perso (`.claude/agents/`)

- `doc-maintainer` — invocable via Task tool, gère tout le workflow doc (HANDOFF, ROADMAP, ADRs, pivot, promotion)
- `worker` — rôle teammate pour les **agent-teams** : exécute une sous-tâche dans son périmètre (idéalement son git worktree), rapporte au lead via `SendMessage`, ne touche pas aux docs partagés ni à la numérotation (voir [§ Agent teams](rules/template-maintenance.md#agent-teams-multi-agent--anti-collision))

---

> 💡 **Exemple complet rempli (référence optionnelle)** : [EXAMPLES/acme-sync-erp-notion-docs/](../EXAMPLES/acme-sync-erp-notion-docs/) — projet ACME (Sync ERP→Notion). Présent dans le **repo template uniquement** (exclu de ton projet par le rsync d'init). À consulter pour voir « à quoi ça ressemble une fois rempli ». Ce n'est **pas** le mécanisme de scaffolding (ça, c'est `/spec` + ses templates bundlés `.claude/skills/spec/templates/`).
