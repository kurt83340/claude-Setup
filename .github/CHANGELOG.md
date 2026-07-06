# Changelog — template claude-Setup

Format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versions [SemVer](https://semver.org/lang/fr/).
Versions du **template lui-même** — distinct du CHANGELOG d'un projet généré (qui vit dans `.claude/docs/CHANGELOG.md`).

## [0.7.0] — 2026-07-06

### Changed

- **Skills n8n hors-cœur remplacés** : les 3 skills d'exemple « jouets » (`n8n-push`, `n8n-seed-db`, `n8n-deploy` — déploiement) laissent place à **7 skills d'expertise n8n réels** dans `EXAMPLES/skills-n8n/` : `n8n-node-configuration`, `n8n-validation-expert`, `n8n-workflow-patterns`, `n8n-code-javascript`, `n8n-code-python`, `n8n-expression-syntax`, `n8n-mcp-tools-expert` (skills de référence auto-invoqués, avec fichiers de support type `DEPENDENCIES.md` / `OPERATION_PATTERNS.md`). Toujours copiés dans `.claude/skills/` par `/init-from-template` (type `automation-n8n`).
- **`cleanup-for-type.py`** : la copie des skills n8n passe d'un **mapping en dur** (3 entrées) à un **glob** `EXAMPLES/skills-n8n/n8n-*` (nouvelle clé de profil `copy_examples_glob` + fonction `copy_glob_from_examples`) → robuste à l'ajout/retrait de skills n8n sans toucher le script.
- Inventaires & doc synchronisés : `.claude/CLAUDE.md`, `.claude/rules/template-maintenance.md`, `USAGE.md`, `.github/README.md`, `EXAMPLES/skills-n8n/README.md`, `.env.example`, `workflows/README.md`.

## [0.6.0] — 2026-07-05

### Added

- **Skill `/adopt-template`** (14e skill cœur) — pendant **brownfield** de `/init-from-template` : greffe le template sur un projet EXISTANT sans jamais rien écraser. Copie via `rsync --ignore-existing` (l'existant gagne toujours), état des lieux détecté (manifests → stack + commandes pré-remplies), merges **diff-par-diff** des collisions (CLAUDE.md user préservé + index just-in-time, settings.json fusionné, .gitignore append), mêmes scripts render/cleanup que l'init (source unique), puis **rétro-remplissage** de la doc depuis le projet : stack.md ← manifests, code-map ← `/codemap`, cadrage ← README existant, ROADMAP ← Phase 0 + scan TODO/FIXME, HANDOFF ← git log, ADRs rétroactifs optionnels (max 2-3 — pas d'archéologie).

### Changed

- Inventaires synchronisés (14 skills cœur) ; `cleanup-for-type.py` : `script-jetable` retire aussi `/adopt-template` ; USAGE § « Projet EXISTANT (brownfield) » ; README repo (variante brownfield).

## [0.5.0] — 2026-07-05

Les « templates d'orchestration » : la chaîne implémentation existait déjà (`/spec` → `/conception` → `/team` → `/feature-done`, chaque maillon suggère le suivant) — cette version ajoute les chaînons manquants + le pipeline debugging.

### Added

- **Skill `/debug "<symptôme>"`** (13e skill cœur) — pipeline debugging : symptôme **verbatim** → REPRODUIRE (test rouge minimal — règle d'or : pas de repro = pas de fix) → explorer (`explore-code` + git log + `explore-memoire`) → hypothèses **discriminées par instrumentation** → fix minimal (la cause, pas le symptôme, sans refacto opportuniste) → suite verte → pérenniser (le test de repro RESTE, `/lecon`, gotcha code-map, CHANGELOG Fixed).
- **Mode TDD dans `/team`** (opt-in, décidé au plan d'équipe) : tasks de tests créées d'abord (assignées à `tester`), tasks d'implémentation **bloquées dessus** (`addBlockedBy`) — back/front font passer au vert sans modifier les tests.
- **Étape PR GitHub dans `/feature-done`** : `gh pr create` selon git-workflow (1 spec = 1 PR, squash, CI verte) ; `git push` reste en permission « ask » ; fallback commit local + tag.
- **Choix SDD/TDD critérisé dans `/conception`** (étape 4) : le mode d'exécution est décidé PAR SPEC et noté dans `plan.md` § Décisions — TDD si comportements spécifiables a priori (logique métier, parsing, contrats d'API) ; tests-après + E2E ciblés si exploratoire — `/team` lit ce choix.

### Changed

- Inventaires synchronisés (13 skills cœur) ; `cleanup-for-type.py` : `script-jetable` retire aussi `/debug`.

## [0.4.0] — 2026-07-05

### Added

- **3 agents explorateurs réutilisables** (lecture seule) : `explore-code` (patterns/points d'intégration en `chemin:ligne`), `explore-docs` (doc officielle à jour — context7 → MCP docs → web, URLs + versions, jamais de mémoire), `explore-memoire` (ADRs/leçons/idées/cadrage — « qu'a-t-on déjà décidé/tenté ? »). Le rôle et le format de rapport vivent dans la définition (source unique) ; `/conception` ne fournit que le brief par spec. Subagents par défaut, teammates en mode visible, invocables hors `/conception` pour toute investigation. Justification : `/conception` tourne à chaque spec → le seuil create-on-demand de réutilisation est atteint par construction.

### Changed

- `reviewer` : couvre explicitement la **revue adverse de plans** (`/conception` étape 5) en plus des diffs.
- Interaction directe user ↔ teammate **vérifiée sur doc officielle** et encodée : l'utilisateur peut répondre dans le pane d'un teammate (les gates de `/conception` peuvent s'y jouer) ; question utilisateur = texte dans le pane + `SendMessage` au lead « en attente décision » ; les prompts de permission remontent TOUJOURS au lead.
- Inventaires synchronisés (9 agents) : `agents/README`, `.claude/CLAUDE.md`, `template-maintenance.md`, rule `agent-teams.md`, `STRUCTURE.md`, README repo. (La variante « planifier dans un pane dédié » reste documentée dans `/conception` § Mode visible — via teammate **ad-hoc**, sans agent supplémentaire.)

## [0.3.0] — 2026-07-05

### Added

- **Skill `/conception <spec-id|macro>`** (12e skill cœur) — le workflow de planification arrêté qui manquait entre `/spec` (scaffold) et `/team` (exécution) : contraintes d'abord (code-map/ADR/leçons), **explorations parallèles par subagents** (code, docs officielles, mémoire projet — rapports sourcés), **2-3 options avec trade-offs** (jamais une seule), décision par l'utilisateur (ADR si structurante), plan avec **un point de vérification exécutable par étape**, tasks **partitionnées par fichiers** (prêtes pour `/team`), **revue adverse à contexte frais**, gel + ROADMAP/HANDOFF. Zéro nouveau type de fichier (remplit research/spec/plan/tasks existants), zéro nouvel agent (le skill est le foyer et orchestre des subagents — doctrine post-audit).

### Changed

- `/spec` : les « prochaines étapes » pointent vers `/conception` (au lieu de « remplir les 4 fichiers à la main »).
- Inventaires synchronisés (12 skills cœur) : `.claude/CLAUDE.md`, `template-maintenance.md`, `USAGE.md` (cheat-sheet + workflow feature complète), `STRUCTURE.md`, README repo ; `cleanup-for-type.py` (le type `script-jetable` retire aussi `/conception`).

## [0.2.1] — 2026-07-05

### Fixed

- **`render.py` (init-from-template) : init silencieusement à vide** — les motifs `EXCLUDE` étaient testés en substring sur le chemin **absolu** ; un projet situé sous un dossier parent nommé comme un motif (ex. `.../test/projetA/`) voyait 100 % de ses fichiers exclus → « 0 fichiers à scanner », 0 substitution, aucune erreur. Découvert au **premier init réel** (projetA, session satellite) et rapatrié ici. Correctif : matching sur le chemin **relatif** à la racine, **ancré sur les frontières de segments** (`latest/` ne matche plus `test/`). Test de régression `test/test_render.py` + step CI.

## [0.2.0] — 2026-07-05

Câblage **agent-teams** complet + **filets mémoire** — objectifs : tout déléguer à des agents visibles sous tmux (préconfigurés ou à la volée, retours à l'orchestrateur), mémoire cross-session qui n'oublie rien.

### Added

- **Agent teams câblés** dans `settings.json` : `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "tmux"` (split panes) ; permissions `git worktree` (add/list/prune en allow ; remove + merge en ask).
- **Rule `.claude/rules/agent-teams.md`** — SOURCE UNIQUE du protocole d'équipe, auto-chargée par toute session (lead ET teammates, y compris ad-hoc) : § Teammate (SendMessage avant idle, périmètre, docs partagés interdits, jamais committer HANDOFF.md), § Lead (politique teammate vs subagent, worktrees, task list native, débrief mémoire OBLIGATOIRE), **cycle de vie lead-owned vs user-owned** (un teammate demandé par l'utilisateur persiste, seul l'utilisateur le ferme ; un teammate auto-invoqué est fermé par le lead après débrief), **topologie hub-and-spoke par défaut / mesh opt-in scopé** (fixée au spawn).
- **Skill `/team <spec-id>`** (11e skill cœur) : préflight → plan d'équipe **validé par l'utilisateur** (rôles + topologie) → tasks natives (miroir de `specs/00X/tasks.md`) → 1 worktree par codeur → spawn → suivi (idle notifications + task list + trace) → **débrief mémoire à chaque rapport** → merge + tests après chaque merge → clôture propre.
- **4 rôles teammate préconfigurés** : `front-end`, `back-end`, `tester`, `reviewer` (lecture seule) — chaque fichier ne porte que sa spécialité, le protocole vient de la rule ; `worker.md` aminci de même (fin de la duplication).
- **Filet « n'oublie rien »** : hook `SessionEnd` (`sessionend-snapshot.py`) snapshotte l'état à CHAQUE fin de session ; `SessionStart(startup)` injecte le filet s'il est plus frais que `HANDOFF.md` (= `/handoff` oublié) puis le **consomme**.
- **Trace d'équipe** : hooks `TaskCreated`/`TaskCompleted`/`TeammateIdle` → `teamtask-log.py` → `.claude/.cache/team-progress.log` (1 ligne JSON/événement, jamais bloquant).
- **`/doc-health` étape 10 — auto-memory** : localise `MEMORY.md` (machine-locale, keyée par repo git — partagée par les worktrees), propose la **promotion** des patterns stables en rule / leçon / ADR (consolidation cache → docs versionnées).
- `snapshot_common.py` : helpers partagés PreCompact/SessionEnd (source unique du format snapshot).
- Suite de tests hooks étendue → **40 tests** (sessionend ×3, injection startup ×5, routing compact, teamtask-log ×5).

### Changed

- `template-maintenance.md` : § Agent teams remplacé par un pointeur vers la rule (single-source) ; § 3 layers enrichi — auto-memory = **cache** (machine-local, écrit en concurrence) → durabilité par promotion via `/doc-health`.
- Inventaires synchronisés : `.claude/CLAUDE.md` (11 skills cœur + roster agents), `USAGE.md` (cheat-sheet, table hooks, § Agent teams), `STRUCTURE.md` (arbres rules/skills/agents), `agents/README.md` (invocation subagent OU teammate), README repo.
- `cleanup-for-type.py` : le type `script-jetable` retire aussi `.claude/skills/team/`.

### Fixed

- Frontmatter `/lecon` : un « : » dans la description cassait le YAML strict (le parser Claude Code le tolère, mais fragile) → remplacé par un tiret.

## [0.1.0] — 2026-06-28

Première mise sous version, après audit complet (cf. `test/AUDIT-2026-06-28.md`).

### Added

- Repo GitHub privé `kurt83340/claude-Setup` + mise sous git.
- Suite de tests des hooks `test/test_hooks.py` (16 tests, stdlib, 0 dépendance).
- Proto de packaging plugin `test/build-plugin.py` (assemble un plugin distribuable, non-destructif).
- Rapport d'audit vérifié `test/AUDIT-2026-06-28.md`.
- CI GitHub Actions (tests hooks + validations structurelles à chaque push).

### Changed

- `CLAUDE.md` → **index just-in-time** : 3 `@-import` (HANDOFF/ROADMAP/code-map) au lieu de 18 ; reste lu à la demande. Mesuré : **~14,6k → ~1,5k tokens** auto-chargés au démarrage (−90 %).
- Hook PreCompact → snapshot dans `.claude/.cache/` (non-versionné, overwrite) au lieu d'être appendé au `HANDOFF.md` versionné. Fin du gonflement (+442 o/compaction avant).
- Réfs GitHub Spec Kit corrigées : `uv tool install specify-cli --from git+…@vX.Y.Z` + commandes `/speckit.*` (au lieu de `npx specify init`).

### Fixed

- `db-migration` : ajout `allowed-tools` + `disable-model-invocation` (frontmatter hors-norme).
- Permissions `/init-from-template` (`python3` scopé / `chmod` / `git init`) et `/spec` (`Bash(cp:*)`) → fin des prompts de permission pendant ces workflows.
- Retrait de la clé de réglage inerte `autoMemory.scope` (seuls `autoMemoryEnabled` / `autoMemoryDirectory` existent).

### Notes

- 2 pistes de l'audit initial **invalidées** après vérification sur la doc officielle : le layout skills à plat est correct (pas de scan récursif pour le regroupement) ; les schémas de hooks (`systemMessage`, stdout SessionStart) sont valides.
