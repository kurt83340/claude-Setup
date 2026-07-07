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
- `/conception <spec-id|macro>` ⭐ — arrêter le plan : explore (subagents code+docs+mémoire) → 2-3 options → décision → plan/tasks + revue adverse
- `/feature-done <spec-id>` ⭐ — livraison feature
- `/pivot "<raison>"` — orchestrer un pivot client (9 étapes)
- `/team <spec-id>` ⭐ — déléguer une feature à une équipe de teammates visibles en tmux (worktrees, task list native, mode TDD opt-in, merge, débrief mémoire)
- `/debug "<symptôme>"` — pipeline de debugging : reproduire (test rouge) → explorer → hypothèses discriminées → fix minimal → test pérennisé + leçon

### Cycle de vie des artefacts (capture/promote/discard/archive)

- `/lecon [mode] <args>` — leçons : `<scope> "<titre>"` | `promote <date>` | `discard <date>` | `archive`
- `/adr [mode] <args>` — ADRs : `<scope> "<titre>"` | `supersede <NN>` | `deprecate <NN>` | `list`
- `/idee [mode] <args>` — idées : `"<titre>"` | `promote <date>` | `discard <date>` | `archive`

### Audit & technique

- `/doc-health` — audit hebdo de la doc
- `/codemap` — régénère `code-map.md` depuis `src/`

### Bootstrap

- `/init-from-template` — initialise un projet depuis ce template (from scratch, UNE FOIS)
- `/adopt-template` — greffe le template sur un projet EXISTANT (brownfield, UNE FOIS) : merges non-destructifs + rétro-remplissage doc depuis l'existant

> 🗂️ **Inventaire canonique** : cette liste (**14 skills cœur**) est la **source de vérité** des skills du template. `README.md`, `USAGE.md` et `.claude/rules/template-maintenance.md` y **renvoient** — ne pas redupliquer ailleurs. Un check CI vérifie que chaque dossier `.claude/skills/*` y figure.

### Skills stack-spécifiques = PLUGINS (marketplace `claude-setup`, dossier `plugins/`)

Hors du cœur. Packagés en **plugins** installés par projet via `/plugin` — **auto-découverts** (aucun listing à maintenir ici) :

- **n8n** (type `automation-n8n`) → plugin **`n8n-expertise`** (7 skills : node-configuration, validation-expert, workflow-patterns, code-javascript, code-python, expression-syntax, mcp-tools-expert) → `claude plugin install n8n-expertise@claude-setup --scope project`
- **BDD / Alembic** (type `bdd-migration`) → plugin **`db-migration`** → `claude plugin install db-migration@claude-setup --scope project`

> Marketplace = ce repo : `/plugin marketplace add kurt83340/claude-Setup`. Source : [`plugins/`](../plugins/) · manifeste : [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json).

Quand un projet ajoute d'autres skills liés à sa stack, les installer dans `.claude/skills/` **et les recenser ici** : ce fichier reste l'inventaire unique de **tous** les skills — cœur ou stack.

## Slash commands projet

> Les « custom commands » (`.claude/commands/`) ont **fusionné avec les skills** — le template
> n'utilise plus que le format skill ([doc officielle](https://code.claude.com/docs/en/skills) :
> "Skills are recommended"). Pour ajouter un `/nom` projet : `.claude/skills/<nom>/SKILL.md`
> (plugins stack : [plugins/](../plugins/)).

## Agent perso (`.claude/agents/`)

- `doc-maintainer` — subagent (Task tool), gère tout le workflow doc (HANDOFF, ROADMAP, ADRs, pivot, promotion)
- `worker` · `front-end` · `back-end` · `tester` · `reviewer` — **rôles teammate** pour les agent-teams (spawnés par le lead, en général via `/team`, visibles en tmux). Protocole commun (SendMessage, périmètre, cycle de vie lead-owned/user-owned, topologie hub-and-spoke/mesh) : source unique [rules/agent-teams.md](rules/agent-teams.md)
- `explore-code` · `explore-docs` · `explore-memoire` — **explorateurs lecture seule réutilisables** (subagents par défaut, teammates en mode visible) : étape Explore de `/conception` + toute investigation ; `reviewer` assure aussi la revue adverse des plans

---

> 💡 **Exemple complet rempli (référence optionnelle)** : [EXAMPLES/acme-sync-erp-notion-docs/](../EXAMPLES/acme-sync-erp-notion-docs/) — projet ACME (Sync ERP→Notion). Présent dans le **repo template uniquement** (exclu de ton projet par le rsync d'init). À consulter pour voir « à quoi ça ressemble une fois rempli ». Ce n'est **pas** le mécanisme de scaffolding (ça, c'est `/spec` + ses templates bundlés `.claude/skills/spec/templates/`).
