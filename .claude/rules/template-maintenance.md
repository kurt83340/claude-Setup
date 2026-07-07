# Template maintenance — Comment vivre avec cette structure

> Méta-documentation : comment ce projet est organisé, comment le maintenir vivant,
> quel skill/agent invoquer pour quelle tâche. Lis ce fichier avant d'écrire dans
> `.claude/docs/` ou `.claude/docs/conception/specs/`.

## Les 3 layers de mémoire (à connaître AVANT tout)

Claude Code 2.1.x a maintenant 3 couches de mémoire qui se complètent. **Ne les confonds pas.**

| Layer           | Fichier                                                                      | Qui l'écrit            | Survit à quoi ?                            | Versionné git ?        |
| --------------- | ---------------------------------------------------------------------------- | ---------------------- | ------------------------------------------ | ---------------------- |
| **1. Stable**   | `CLAUDE.md` (projet) + `.claude/CLAUDE.md` (template) + `.claude/rules/*.md` | Toi (humain)           | Toujours                                   | ✅ Oui                 |
| **2. Patterns** | `~/.claude/projects/<projet>/memory/MEMORY.md`                               | Claude (auto)          | Sessions, compaction, /clear               | ❌ Non (machine-local) |
| **3. État**     | `.claude/docs/HANDOFF.md`                                                    | `/handoff` skill + toi | Sessions, compaction (via hook PreCompact) | ✅ Oui                 |

**Auto-memory (layer 2) est ACTIF par défaut depuis v2.1.59.** Claude écrit tout seul ce qu'il apprend : conventions, build commands, debugging, préférences. Tu n'as rien à faire — c'est dans `~/.claude/projects/...`.

⚠️ **Layer 2 = un cache, pas une garantie** : machine-local, non versionné, keyé par repo git
(les worktrees le partagent), écrit en concurrence si plusieurs sessions tournent en parallèle.
Le « n'oublie rien » durable passe par la **promotion** vers les couches versionnées :
`/doc-health` (étape auto-memory) propose de promouvoir les patterns stables en rule / leçon / ADR.

**Quoi mettre où ?**

- Règles **invariantes** du projet → `.claude/rules/*.md` (humain-écrit, versionné)
- Patterns **appris** automatiquement → MEMORY.md (laisse Claude faire)
- **État volatile** (où j'en suis, blockers, next steps) → .claude/docs/HANDOFF.md (court, narratif)

**Pour reprendre une session précise** : utilise `/resume` (fidélité 100%, garde tout le contexte). .claude/docs/HANDOFF.md est complémentaire — il sert quand tu changes de machine, partages avec un collègue, ou démarres une session fraîche dans un repo cloné.

## La structure en 30 secondes

- **Racine** : config + livrables (`CLAUDE.md` = **le projet**, `README.md`, `.env.example`, `.gitignore`, `workflows/`)
- **`.claude/`** : matière première du projet (TOUT le reste)
  - `CLAUDE.md` = **le template** (comment il vit, skills, agent) — distinct du `CLAUDE.md` racine
  - `rules/`, `skills/`, `agents/`, `settings.json` : Claude config
  - `.claude/docs/cadrage/` : capture initiale + évolutions/pivots (input externe)
  - `.claude/docs/conception/` : design macro (research, PRD, ARCHITECTURE, tasks) **+ specs/ (design micro par feature)**
  - `.claude/docs/` (racine) : fichiers vivants (HANDOFF, ROADMAP, CHANGELOG, ACCESS) + transversaux (adr/, idees/)
- **Racine projet** : `src/` (code, créé quand tu codes), `workflows/` (livrables n8n), config (`.env.example`, `.gitignore`)

> 🪧 **Deux `CLAUDE.md`, tous deux chargés à chaque session :**
>
> - **racine `CLAUDE.md`** = _le projet_ (résumé, navigation doc, conventions, reminders).
> - **`.claude/CLAUDE.md`** = _le template_ (comment il vit, **tous** les skills — template + hors-template type n8n —, agent).
>
> Règle : info **projet** → racine ; info **template / outillage** → `.claude/CLAUDE.md`. ⚠️ Dans `.claude/CLAUDE.md`, les `@-import` sont relatifs à `.claude/` (ex. `@rules/template-maintenance.md`, pas `@.claude/rules/…`).

**Pattern mirror macro ↔ micro :**

| Macro (`.claude/docs/conception/`) | Micro (`.claude/docs/conception/specs/00X-feature/`) | Question                                |
| ---------------------------------- | ---------------------------------------------------- | --------------------------------------- |
| `research.md`                      | `research.md`                                        | Quelles options on a explorées ?        |
| `PRD.md`                           | `spec.md`                                            | Qu'est-ce qu'on construit et pourquoi ? |
| `ARCHITECTURE.md`                  | `plan.md`                                            | Comment on l'implémente ?               |
| `tasks.md` (plan MVP)              | `tasks.md`                                           | Quoi exécuter et dans quel ordre ?      |

→ `.claude/docs/ROADMAP.md` (racine) = **dashboard vivant** qui synthétise l'état (status, blockers).

## Les fichiers vivants (à maintenir activement, RACINE .claude/docs/)

| Fichier                          | Fréquence MAJ                                                                  | Qui le met à jour                                                |
| -------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| `.claude/docs/HANDOFF.md` ⭐     | **Chaque fin de session**                                                      | Via `/handoff` (skill)                                           |
| `.claude/docs/ROADMAP.md`        | Démarrage + fin de feature                                                     | Via `/feature-done` ou manuel                                    |
| `.claude/docs/CHANGELOG.md`      | Chaque feature livrée + bug fixé                                               | Manuel ou via `/feature-done`                                    |
| `.claude/docs/ACCESS.md`         | Quand un accès change de statut                                                | Manuel                                                           |
| `.claude/docs/cadrage/README.md` | À chaque pivot / nouveau contexte client                                       | Manuel                                                           |
| `.claude/docs/lecons.md`         | À chaque bug/pattern/observation                                               | Append manuel, review hebdo                                      |
| `.claude/docs/code-map.md` ⭐    | Nouvelle règle de couplage / contrainte d'archi / gotcha (PAS le file-by-file) | Manuel ou `/codemap` ; hook PreToolUse réinjecte les contraintes |
| `.claude/docs/stack.md`          | À chaque nouvelle lib / service tiers / LLM utilisé                            | Manuel                                                           |

## Les fichiers semi-stables (modifiés sur événements importants)

| Fichier                                   | Quand le toucher                                           |
| ----------------------------------------- | ---------------------------------------------------------- |
| `.claude/docs/conception/research.md`     | Append section datée à chaque pivot/exploration ultérieure |
| `.claude/docs/conception/PRD.md`          | Version bump (v1.1, v2…) lors de pivots majeurs            |
| `.claude/docs/conception/ARCHITECTURE.md` | Décision archi majeure (souvent accompagnée d'un ADR)      |
| `.claude/docs/GLOSSARY.md`                | Ajout d'un nouveau terme métier                            |
| `.claude/docs/RUNBOOK.md`                 | Après chaque incident ou nouvelle procédure                |
| `.claude/docs/adr/00XX-*.md`              | **IMMUABLE** — créer un nouvel ADR qui le supersede        |

## Workflow fin de session (CRITIQUE)

À chaque fois que tu finis une session de travail, suis ce protocole :

```
1. Vérifier git status   → quels fichiers modifiés ?
2. Lancer les tests      → ce qui marche / casse
3. Update .claude/docs/HANDOFF.md     → status, next steps, blockers
4. Si feature livrée :
   - Cocher dans .claude/docs/ROADMAP.md
   - Ajouter entrée .claude/docs/CHANGELOG.md
   - Suggérer ADR si décisions structurantes
5. Commit si pertinent (NE PAS push sans validation user)
```

**Préférer** : invoquer `/handoff` (skill) qui fait tout ça automatiquement.

## Workflow début de session

```
1. Lire .claude/docs/HANDOFF.md       → reprendre où on en est
2. Lire .claude/docs/ROADMAP.md       → vue d'avion du projet
3. Lire la spec en cours (lien dans HANDOFF)
4. git status + git log -5 → ce qui s'est passé
5. Demander à l'user : "on continue sur X ? ou autre chose ?"
```

## Quand créer un nouveau fichier ?

**Règle d'or :** crée à la demande, JAMAIS préventivement.

| Trigger                                                                             | Fichier à créer                                                                                                    |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| User mentionne credentials/API/OAuth → pas d'ACCESS.md                              | Créer `.claude/docs/ACCESS.md`                                                                                     |
| User parle de déploiement prod imminent                                             | Créer `.claude/docs/RUNBOOK.md`                                                                                    |
| Décision tech qui impacte plusieurs features OU survit à la feature                 | Créer `.claude/docs/adr/00XX-<scope>-titre.md` (voir convention ci-dessous)                                        |
| Décision tech **locale à UNE feature** (choix de lib pour cette feature uniquement) | Section `## Décisions` dans `specs/00X/plan.md` (PAS d'ADR séparé)                                                 |
| > 3 références à un terme métier non documenté                                      | Créer/enrichir `.claude/docs/GLOSSARY.md`                                                                          |
| Démarrage d'une feature                                                             | Créer `.claude/docs/conception/specs/00X-feature/{research,spec,plan,tasks}.md`                                    |
| Nouvelle idée pas mûre                                                              | Créer `.claude/docs/idees/YYYY-MM-DD-idee.md`                                                                      |
| Bug / pattern / observation à capturer                                              | Append dans `.claude/docs/lecons.md` (statut 🆕 new, décider promotion plus tard)                                  |
| **Avant d'éditer un fichier de code**                                               | **Vérifier les règles de couplage dans `.claude/docs/code-map.md`** (le rôle/les imports : se lisent dans le code) |
| Nouvelle règle de couplage / contrainte d'archi / gotcha découvert                  | MAJ `.claude/docs/code-map.md` (PAS de description fichier-par-fichier — déductible + drift)                       |
| Nouvelle lib Python / service tiers (Sentry, Slack…) / LLM utilisé                  | MAJ `.claude/docs/stack.md` (table appropriée)                                                                     |
| Doc reçue du client                                                                 | Archiver dans `.claude/docs/cadrage/documents/` avec date                                                          |
| Compte-rendu de réunion                                                             | Créer `.claude/docs/cadrage/reunions/YYYY-MM-DD-titre.md`                                                          |
| Ticket Jira/Linear/Asana reçu                                                       | Créer `.claude/docs/cadrage/tickets/TICKET-XXX-titre.md`                                                           |
| Diagramme business simple                                                           | Inline ASCII dans `cadrage/README.md`                                                                              |
| Diagramme business complexe                                                         | `cadrage/diagrams/X.excalidraw` + export `.svg` à côté                                                             |
| Diagramme technique simple                                                          | Inline ASCII dans `conception/ARCHITECTURE.md`                                                                     |
| Diagramme technique gros                                                            | `conception/diagrams/X.excalidraw` + export `.svg`                                                                 |
| Diagramme spécifique à une feature                                                  | Inline dans `specs/00X/plan.md` ou `specs/00X/diagrams/` (rare)                                                    |

## Convention ADR (Architecture Decision Records)

**Naming** : `00XX-<scope>-<titre-court>.md` — scope dans le nom pour lisibilité immédiate.

**5 scopes** :
| Scope | Pour quoi |
|---|---|
| `cadrage` | Contraintes capturées au début (souvent imposées par le client) |
| `mvp` | Décisions structurantes au niveau projet entier |
| `feature-00X` | Décisions **réutilisables** spécifiques à une feature (rare) |
| `infra` | Hébergement, déploiement, secrets, monitoring |
| `operations` | Décisions post-prod (incidents, runbook) |

**Frontmatter obligatoire** (machine-lisible) :

```yaml
---
status: accepted # proposed | accepted | deprecated | superseded
scope: mvp
phase: 2026-Q2
supersedes: null # ou 0003
---
```

**Règle critique : ADR vs section `## Décisions` dans `plan.md`**

| Niveau de décision                          | Où l'écrire                                      |
| ------------------------------------------- | ------------------------------------------------ |
| Cross-feature (impacte > 1 spec)            | ADR global `.claude/docs/adr/`                   |
| Survit à la mort de la feature              | ADR global `.claude/docs/adr/`                   |
| Locale à UNE feature (lib, pattern interne) | Section `## Décisions` dans `specs/00X/plan.md`  |
| Devient cross-feature plus tard             | **Promouvoir** depuis plan.md → créer ADR global |

**Changement d'avis** : créer un nouvel ADR avec `supersedes: 00XX`, l'ancien passe en `status: superseded`. Ne JAMAIS éditer un ADR existant.

Détails complets : [@.claude/docs/adr/README.md](.claude/docs/adr/README.md)

## Convention diagrammes (3 formats)

| Format                       | Quand                                      | Claude-friendly ?         |
| ---------------------------- | ------------------------------------------ | ------------------------- |
| **ASCII inline** dans le .md | Default — diagrammes simples (flow, arbre) | ✅ Parfait                |
| **Excalidraw + export SVG**  | Diagrammes visuels complexes               | ⚠️ SVG via Read explicite |
| **PNG/JPG**                  | Screenshots, photos uniquement             | ⚠️ Pas fiable en 2026     |

**Règle d'or images :** commit **la SOURCE éditable + l'EXPORT SVG/PNG** côte à côte.

```
diagrams/
├── flow-X.excalidraw    # source éditable (humain)
└── flow-X.svg           # export (Claude + GitHub preview)
```

⚠️ `![](path)` dans un .md n'est PAS auto-suivi par Claude. Pour qu'il "voit" un diagramme image, il faut un Read explicite ou pointer vers un .md ASCII.

## Quel skill / agent appeler ?

### Skills perso (`.claude/skills/`)

> 🗂️ **Inventaire canonique** (liste + 1-ligne + chemin) → [`.claude/CLAUDE.md`](../CLAUDE.md). Ici = **quand** invoquer. Les skills stack-spécifiques (`db-migration`, `n8n-expertise`) sont des **plugins** (marketplace `claude-setup`, dossier `plugins/`), installés par projet via `/plugin`.

#### Session & feature

| Skill                      | Quand l'invoquer                                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `/init-from-template` ⭐   | UNE FOIS, début de projet from scratch — substitue les CORE placeholders (UPPER_SNAKE)                              |
| `/adopt-template`          | UNE FOIS, projet EXISTANT (brownfield) — merges non-destructifs + rétro-remplissage doc depuis l'existant           |
| `/handoff` ⭐              | Fin de session — snapshot .claude/docs/HANDOFF.md (status + échecs + blockers + next)                               |
| `/spec "<titre>"` ⭐       | Démarrer une feature — scaffold 4 fichiers (research/spec/plan/tasks) + ROADMAP                                     |
| `/conception <spec-id>` ⭐ | Arrêter le plan — explore par subagents (code/docs/mémoire), 2-3 options, décision, plan vérifiable + revue adverse |
| `/feature-done <id>` ⭐    | Après livraison feature — coche ROADMAP + CHANGELOG + ADRs + archive idées                                          |
| `/pivot "<raison>"`        | Workflow pivot client 9 étapes orchestrées                                                                          |
| `/team <spec-id>` ⭐       | Déléguer une feature à une équipe de teammates (tmux) — worktrees, task list, mode TDD opt-in, débrief              |
| `/debug "<symptôme>"`      | Bug non trivial — reproduire (test rouge) → explorer → hypothèses → fix minimal → test pérennisé + leçon            |

#### Cycle de vie d'artefacts (capture/promote/discard/archive — sous-modes unifiés)

| Skill    | Sous-modes                                                                           |
| -------- | ------------------------------------------------------------------------------------ |
| `/lecon` | `<scope> "<titre>"` (capture) / `promote <date>` / `discard <date>` / `archive`      |
| `/adr`   | `<scope> "<titre>"` (capture) / `supersede <NN>` / `deprecate <NN>` / `list [scope]` |
| `/idee`  | `"<titre>"` (capture) / `promote <date>` / `discard <date>` / `archive`              |

#### Audit & technique

| Skill         | Quand l'invoquer                                                                       |
| ------------- | -------------------------------------------------------------------------------------- |
| `/doc-health` | Audit hebdo — docs stale + ADRs manquants + growth + leçons en attente + specs stalled |
| `/codemap`    | Après gros refacto — régénère .claude/docs/code-map.md depuis le code                  |

### Slash commands projet

> **Les « custom commands » (`.claude/commands/`) ont fusionné avec les skills** (même moteur,
> même frontmatter, même invocation auto via `description`). La doc officielle recommande le
> format skill ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)) —
> **le template n'utilise plus que `.claude/skills/<nom>/SKILL.md`**.
> Pour un `/nom` sensible (deploy…) : `disable-model-invocation: true` = slash-only.

**Plugins stack disponibles** : plugin `n8n-expertise` (7 skills n8n, type `automation-n8n`) et plugin `db-migration` (Alembic, type `bdd-migration`) — dans `plugins/` (marketplace `claude-setup`), installés par projet via `/plugin install …@claude-setup` (auto-découverts).

> **Pas de namespacing par dossier en 2026** : Claude Code scanne `.claude/skills/<nom>/SKILL.md` à **1 niveau uniquement** (cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192), feature request OPEN). Si tu veux grouper des skills par thème → utilise des **préfixes de nom** (ex: `n8n-deploy`, `n8n-test`) ou package-les en **plugin** (`/<plugin>:<skill>`).

### Agent perso (`.claude/agents/`)

| Agent                                                       | Quand l'invoquer                                                                                                                                                                                                                                                           |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `doc-maintainer`                                            | Via Task tool. Couvre HANDOFF, ROADMAP, CHANGELOG, ADRs, **pivot 9-étapes**, **promotion lecon→ADR**, **archivage idées**. Diff par diff, jamais d'overwrite.                                                                                                              |
| `worker` / `front-end` / `back-end` / `tester` / `reviewer` | **Agent-teams** : rôles teammate (généraliste, UI, serveur, QA, review lecture-seule — diffs ET plans), spawnés par le lead — en général via `/team`. Protocole commun (SendMessage, périmètre, cycle de vie, topologie) : source unique [agent-teams.md](agent-teams.md). |
| `explore-code` / `explore-docs` / `explore-memoire`         | **Explorateurs réutilisables** (lecture seule) — code en `chemin:ligne`, docs externes (context7→MCP→web), mémoire projet (ADRs/leçons). Subagents par défaut, teammates en mode visible. Utilisés par `/conception`, invocables pour toute investigation.                 |

### Skills built-in Claude Code utiles

| Skill                | Pour quoi                                                           |
| -------------------- | ------------------------------------------------------------------- |
| `/security-review`   | Avant chaque push prod (vérif sécurité changes courants)            |
| `/code-review`       | Avant merge d'une feature complexe                                  |
| `/init`              | NE PAS utiliser (ce template a déjà CLAUDE.md)                      |
| `/resume`            | Reprendre session précise (fidélité 100%) — complémentaire HANDOFF  |
| `/loop 10m /handoff` | Optionnel : auto-update HANDOFF toutes les 10 min en session longue |

## ✅ Skills + hooks + agents EN PLACE

### Skills perso disponibles

| Skill                    | Quoi                                                                                                                                                                                   | Path                                 |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `/init-from-template` ⭐ | Pose 10 questions, substitue les CORE placeholders + lance cleanup-for-type.py adapté au type projet (à exécuter UNE FOIS)                                                             | `.claude/skills/init-from-template/` |
| `/adopt-template`        | Brownfield : état des lieux détecté, merges diff-par-diff (CLAUDE.md/settings/.gitignore existants), mêmes scripts render/cleanup, rétro-remplissage doc (stack/code-map/HANDOFF/ADRs) | `.claude/skills/adopt-template/`     |
| `/handoff` ⭐            | Snapshot .claude/docs/HANDOFF.md fin de session (status + échecs + blockers + next). Détecte HANDOFF fresh (post-init)                                                                 | `.claude/skills/handoff/`            |
| `/spec` ⭐               | Scaffold nouvelle feature : 4 fichiers research/spec/plan/tasks depuis templates + update ROADMAP                                                                                      | `.claude/skills/spec/`               |
| `/conception` ⭐         | Méthode de planification : explorations parallèles (subagents), tableau d'options, décision user, plan avec points de vérification, revue adverse                                      | `.claude/skills/conception/`         |
| `/feature-done` ⭐       | Coche ROADMAP + CHANGELOG + HANDOFF + suggère ADRs + archive idées + marque leçons promues                                                                                             | `.claude/skills/feature-done/`       |
| `/doc-health`            | Audit hebdo : docs stale, ADRs manquants, growth opportunities, code-map drift, specs stalled, leçons en attente                                                                       | `.claude/skills/doc-health/`         |
| `/lecon`                 | Ajoute entry rapide dans .claude/docs/lecons.md (statut 🆕 new) + workflow promotion documenté                                                                                         | `.claude/skills/lecon/`              |
| `/idee`                  | Capture/gère les idées perso (`idees/`) — capture / promote (→ spec) / discard / archive                                                                                               | `.claude/skills/idee/`               |
| `/codemap`               | MAJ .claude/docs/code-map.md : vue macro + règles de couplage + gotchas, et détecte les violations de couplage (scan imports). PAS de file-by-file.                                    | `.claude/skills/codemap/`            |
| `/adr`                   | Crée un nouveau ADR (frontmatter + structure + index README) + gère pattern supersede                                                                                                  | `.claude/skills/adr/`                |
| `/pivot`                 | Workflow pivot client 9 étapes (réunion → cadrage → research → PRD bump → tasks refonte → ROADMAP v2 → ADR → leçon → HANDOFF)                                                          | `.claude/skills/pivot/`              |
| `/team` ⭐               | Orchestre une équipe de teammates (tmux) sur une feature : plan validé, worktrees, task list native, mode TDD opt-in, suivi, merge, débrief mémoire                                    | `.claude/skills/team/`               |
| `/debug`                 | Pipeline debugging : symptôme verbatim → repro (test rouge) → hypothèses discriminées → fix minimal → test pérennisé + leçon                                                           | `.claude/skills/debug/`              |

> 🧩 Skills **stack** = plugins : `db-migration` (Alembic) + `n8n-expertise` (×7) → dossier `plugins/`, marketplace `claude-setup`. Installés par projet via `/plugin install …@claude-setup`, auto-découverts (pas de listing manuel). Inventaire cœur → [`.claude/CLAUDE.md`](../CLAUDE.md).

### Hooks configurés (cf `.claude/settings.json`)

| Hook                                             | Quoi                                                                                                          | Script                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `PreCompact` ⭐                                  | Snapshot pré-compaction dans `.claude/.cache/` (non-versionné, overwrite) + marker `/tmp/`                    | `hooks/precompact-snapshot-handoff.py`  |
| `SessionStart(matcher: compact)`                 | Re-inject le snapshot (depuis `.claude/.cache/`) après compaction                                             | `hooks/sessionstart-inject-handoff.py`  |
| `SessionEnd` ⭐                                  | Filet « n'oublie rien » : snapshot d'état à CHAQUE fin de session (cache, overwrite)                          | `hooks/sessionend-snapshot.py`          |
| `SessionStart(matcher: startup)`                 | Injecte le filet fin-de-session s'il est plus frais que HANDOFF.md, puis le consomme                          | `hooks/sessionstart-inject-handoff.py`  |
| `PreToolUse(Edit\|Write)` ⭐                     | Réinjecte les règles de couplage + intention + gotchas (non-déductibles) avant édition de code (cap 4k chars) | `hooks/pretooluse-inject-codemap.py`    |
| `PostToolUse(Edit\|Write)`                       | Détecte triggers (API_KEY, deploy, RGPD) → flag dans `.growth-suggestions.md`                                 | `hooks/posttooluse-growth-detection.py` |
| `Stop`                                           | Rappel `/handoff` si .claude/docs/HANDOFF.md > 24h + changements git pending                                  | `hooks/stop-handoff-reminder.sh`        |
| `TaskCreated` / `TaskCompleted` / `TeammateIdle` | Trace JSON de progression d'équipe dans `.claude/.cache/team-progress.log`                                    | `hooks/teamtask-log.py`                 |

⚠️ **Prérequis** : `chmod +x .claude/hooks/*.py .claude/hooks/*.sh` (sinon les hooks bloquent). Géré automatiquement par `/init-from-template` étape 0.

### Agent perso

| Agent                                                       | Quoi                                                                                                                                                                 |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `doc-maintainer`                                            | Cerveau invocable (Task tool) — couvre HANDOFF, ROADMAP, CHANGELOG, ADRs, pivot 9-étapes, promotion lecon → ADR, archivage idées. Diff par diff, jamais d'overwrite. |
| `worker` / `front-end` / `back-end` / `tester` / `reviewer` | Rôles teammate agent-teams (spawn via `/team` ou à la demande) — protocole commun : [agent-teams.md](agent-teams.md).                                                |
| `explore-code` / `explore-docs` / `explore-memoire`         | Explorateurs lecture seule réutilisables (subagents ou teammates) — étape Explore de `/conception` + toute investigation.                                            |

## Distinction `cadrage/` vs `idees/`

- **`cadrage/`** = ce qu'ON ME FILE (client, collègue, ticket Jira, mail, PDF)
- **`idees/`** = ce que MOI je brainstorme (idée perso, exploration)

→ Jamais mélanger. Si user dit "j'ai eu une idée", c'est `idees/`. Si user dit "voici la doc/le ticket", c'est `cadrage/`.

## Conventions de naming

- **Specs** : `001-feature-name`, `002-...`, séquentiel sans reset (continuera 020, 021…)
- **ADR** : `00XX-<scope>-<titre-court>.md` (ex: `0007-mvp-stack-bdd.md`), séquentiel sans reset, 5 scopes obligatoires
- **Réunions / pivots** : `cadrage/reunions/YYYY-MM-DD-titre.md` (date ISO)
- **Sources reçues** : `cadrage/documents/YYYY-MM-DD-description.ext`
- **Idées perso** : `idees/YYYY-MM-DD-titre-court.md`
- **Leçons** : entries `## YYYY-MM-DD — <titre>` dans `.claude/docs/lecons.md`
- **Tags git** : `vYYYY.MM.DD-HHMM` (tag de déploiement)

## Conventions de statut (ROADMAP)

- `[ ]` = planifié, pas commencé
- `[~]` = en cours (mettre en **gras** pour visibilité)
- `[x]` = livré

## Pattern .claude/docs/HANDOFF.md (format minimal)

```markdown
# HANDOFF — YYYY-MM-DD HHhMM

**Branche** : feature/00X-name
**Spec en cours** : [path/to/spec](path)
**Goal** : ce que je voulais faire cette session
**Status** : tasks X/Y, build OK/KO
**Décisions récentes** : ...
**Échecs tentés** : ce qui n'a pas marché (CRUCIAL)
**Blocked on** : aucun ou X
**Next** : 3 prochaines steps concrètes
```

## Pattern ADR (format minimal)

```markdown
# 00XX — Titre

**Statut :** Proposed | Accepted | Deprecated | Superseded by 00YY
**Date :** YYYY-MM-DD
**Décideur :** Nom

## Contexte

## Options considérées

## Décision

## Conséquences
```

## Ce qu'il NE FAUT PAS faire

- ❌ Créer un fichier "au cas où" (= ça pourrit)
- ❌ Mélanger cadrage/ et idees/
- ❌ Modifier un ADR passé (créer un nouveau qui le supersede)
- ❌ Mettre des credentials dans le repo (.env est gitignored, valeurs ailleurs)
- ❌ Bug log séparé (tout va dans CHANGELOG)
- ❌ Skip le HANDOFF en fin de session (= perte de contexte garantie)
- ❌ Créer RUNBOOK avant la première mise en prod (= ça pourrit)
- ❌ Créer STAKEHOLDERS.md si < 5 personnes (= dans BRIEF suffit)

## Ce qu'il FAUT faire

- ✅ Lire .claude/docs/HANDOFF.md au démarrage de chaque session
- ✅ Update .claude/docs/HANDOFF.md à la fin de chaque session (via `/handoff` idéalement)
- ✅ Numéroter spec/ADR continûment (jamais de reset)
- ✅ Dater les fichiers de .claude/docs/idees/, .claude/docs/cadrage/reunions/, .claude/docs/cadrage/documents/
- ✅ Référencer les ADRs depuis les specs concernées
- ✅ Mettre à jour ROADMAP **à chaque** changement d'état de feature
- ✅ Garder le `CLAUDE.md` racine court & centré projet (< 60 lignes) ; template & skills → `.claude/CLAUDE.md` ; détail → `@.claude/rules/*.md`
- ✅ Préférer un ADR à un long commit message pour les décisions structurantes

## Agent teams (multi-agent) — anti-collision

> **Source unique du protocole** (lead / teammate, cycle de vie lead-owned vs user-owned,
> topologie hub-and-spoke vs mesh, worktrees, débrief mémoire, hooks) :
> [agent-teams.md](agent-teams.md) — une rule auto-chargée, comme celle-ci. Ne pas redupliquer ici.
>
> Câblage : `settings.json` (`env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` + `teammateMode: "tmux"`).
> Orchestration d'une feature : skill `/team`. Rôles teammate : `.claude/agents/` (worker,
> front-end, back-end, tester, reviewer, explore-\*).
>
> Résumé en 3 lignes : le **lead** écrit les docs partagés et alloue les numéros specs/ADR ;
> les **teammates** rapportent via `SendMessage` (jamais leur texte de réponse) et codent
> chacun dans leur **worktree** ; chaque rapport est **débriefé en mémoire** (leçons /
> code-map / HANDOFF) sinon le savoir meurt avec la session teammate.
