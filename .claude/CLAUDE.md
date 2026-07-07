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
- `/feature "<titre>" [pipeline]` ⭐ — dérouler le **pipeline complet** (standard/tdd/custom) en enchaînant les maillons, gate utilisateur entre chaque étape
- `/feature-done <spec-id>` ⭐ — livraison feature
- `/pivot "<raison>"` — orchestrer un pivot client (9 étapes)
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
- **Équipe d'exécution** (toute stack, opt-in) → plugin **`agent-teams`** : `/agent-teams:team` + rôles `worker`/`front-end`/`back-end`/`tester` + hook de trace → `claude plugin install agent-teams@claude-setup --scope project`

> Marketplace = le repo template : `/plugin marketplace add kurt83340/claude-Setup` (une fois), puis `/plugin install <plugin>@claude-setup`. La source (`plugins/` + `.claude-plugin/marketplace.json`) vit dans le repo template — pas dans les projets générés.

Quand un projet ajoute d'autres skills liés à sa stack, les installer dans `.claude/skills/` **et les recenser ici** : ce fichier reste l'inventaire unique de **tous** les skills — cœur ou stack.

## 🔁 Pipelines récurrents (orchestrés par `/feature`)

- **standard** : Planifier (`/spec`+`/conception`) → Coder (solo | `/agent-teams:team`) → Tester → Review adverse → Vérifier → Persister (`/feature-done`)
- **tdd** : Planifier → **Écrire les tests (rouges)** → Coder (vert, sans toucher aux tests) → Review adverse → Vérifier → Persister
- **n8n** : Planifier (pattern via `n8n-workflow-patterns`) → Construire (n8n-mcp + skills `n8n-expertise`) → Valider → Tester en réel → Review adverse (export JSON) → Persister (JSON versionné dans `workflows/`)
- **bug** : `/debug` — Reproduire (test rouge) → Explorer → Hypothèses discriminées → Fix minimal → Pérenniser (leçon)

> **1 pipeline = 1 fichier déposable** dans `.claude/skills/feature/pipelines/` — ajoutes-en au fil de l'eau (format documenté dans le SKILL `/feature`). `/conception` note le mode (TDD/standard) par spec dans `plan.md § Décisions` → `/feature` le lit pour auto-choisir.

## Slash commands projet

> Les « custom commands » (`.claude/commands/`) ont **fusionné avec les skills** — le template
> n'utilise plus que le format skill ([doc officielle](https://code.claude.com/docs/en/skills) :
> "Skills are recommended"). Pour ajouter un `/nom` projet : `.claude/skills/<nom>/SKILL.md`
> (plugins stack : [plugins/](../plugins/)).

## Agent perso (`.claude/agents/`)

- `doc-maintainer` — subagent (Task tool), gère tout le workflow doc (HANDOFF, ROADMAP, ADRs, pivot, promotion)
- `reviewer` — teammate/subagent **lecture seule** : revue adverse des plans (`/conception`) + review des diffs d'équipe. Les **rôles d'exécution** (`worker` · `front-end` · `back-end` · `tester`) + `/agent-teams:team` + hook de trace = **plugin `agent-teams`**. Protocole commun (SendMessage, périmètre, cycle de vie, topologie) : source unique [rules/agent-teams.md](rules/agent-teams.md)
- `explore-code` · `explore-docs` · `explore-memoire` — **explorateurs lecture seule réutilisables** (subagents par défaut, teammates en mode visible) : étape Explore de `/conception` + toute investigation ; `reviewer` assure aussi la revue adverse des plans

---

> 💡 **Exemple complet rempli (référence optionnelle)** : [EXAMPLES/acme-sync-erp-notion-docs/](../EXAMPLES/acme-sync-erp-notion-docs/) — projet ACME (Sync ERP→Notion). Présent dans le **repo template uniquement** (exclu de ton projet par le rsync d'init). À consulter pour voir « à quoi ça ressemble une fois rempli ». Ce n'est **pas** le mécanisme de scaffolding (ça, c'est `/spec` + ses templates bundlés `.claude/skills/spec/templates/`).
