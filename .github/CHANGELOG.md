# Changelog — template claude-Setup

Format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versions [SemVer](https://semver.org/lang/fr/).
Versions du **template lui-même** — distinct du CHANGELOG d'un projet généré (qui vit dans `.claude/docs/CHANGELOG.md`).

## [0.11.0] — 2026-07-07

Étape 2 du plan plugins : l'**exécution d'équipe** sort du cœur — un projet solo/n8n n'embarque plus les rôles web.

### Added

- **Plugin `agent-teams`** (3e plugin du marketplace) : skill **`/agent-teams:team`** (orchestration tmux — plan validé, worktrees, task list native, TDD opt-in, merge, débrief mémoire) + **rôles d'exécution** `worker`/`front-end`/`back-end`/`tester` + **hook de trace** `teamtask-log` (TaskCreated/TaskCompleted/TeammateIdle via `hooks.json` du plugin). Install : `claude plugin install agent-teams@claude-setup --scope project`.
- Matrice « quand créer un fichier » : trigger **STAKEHOLDERS.md** (> 4-5 interlocuteurs → modèle prêt dans STRUCTURE.md § STAKEHOLDERS) — clôt **F9**, le dernier item du backlog TEST-REPORT.

### Changed

- **Restent dans le cœur** (dépendances des skills cœur) : `reviewer` (revue adverse `/conception` + diffs d'équipe), les 3 explorateurs, la rule `agent-teams.md` (protocole, SOURCE UNIQUE) et le câblage `settings.json` (flag agent-teams + `teammateMode` — inertes sans le plugin). **13 skills cœur** (comptes et inventaires synchronisés : `.claude/CLAUDE.md`, README repo, USAGE, STRUCTURE, template-maintenance, agents/README).
- `settings.json` : hooks TaskCreated/TaskCompleted/TeammateIdle retirés (livrés par le plugin) ; `test_hooks.py` teste le hook à son emplacement plugin ; CI : la garde SendMessage couvre aussi `plugins/*/agents/*.md`.

### Removed

- **`test/build-plugin.py`** (proto « tout-`.claude/`-en-un-plugin ») — supplanté par le vrai marketplace `claude-setup` : les composants distribuables sont désormais des plugins dédiés (`plugins/`), le cœur reste un scaffold copié par rsync+init (rules, docs et settings ne sont pas transportables en plugin).

## [0.10.0] — 2026-07-07

### Added

- **Rule `doc-lookup.md`** (SOURCE UNIQUE, auto-chargée) : politique de recherche de doc externe pour toute session, skill et agent — **jamais de réponse de mémoire** pour une API/version ; ordre **context7 (MCP)** → autres MCP docs → WebFetch/WebSearch ; toute affirmation sourcée (version + URL) ; recherche large → `explore-docs`. context7 supposé connecté **user-level** (fallback web sinon).

### Changed

- **Câblage de la politique là où elle manquait** : `/debug` étape 2 spawn aussi `explore-docs` quand une lib/API externe est en jeu (+ `mcp__context7` dans ses allowed-tools) ; `mcp__context7` ajouté aux **5 rôles teammate** (`worker`, `front-end`, `back-end`, `tester`, `reviewer`) — doc versionnée en direct sans ouvrir le web aux codeurs ; pointeurs vers la rule dans `explore-docs`, le plugin `db-migration` (doc Alembic à jour), le `CLAUDE.md` racine (liens conventions), `STRUCTURE.md` (arbre rules/) ; prérequis « MCP context7 user-level » documenté dans USAGE. (`/conception` + `explore-docs` étaient déjà câblés.)

## [0.9.1] — 2026-07-07

Post-review complète (workflow multi-agents : 15 findings confirmés + vérifs inline + sweep) — durcissement init/adopt et correctifs de cohérence.

### Fixed

- **🔴 `/adopt-template` détruisait les dossiers du PROJET** : `strip_template_maintenance` supprimait sans condition `.github/`, `test/`, `plugins/` — or en brownfield ils appartiennent à l'**utilisateur** (le rsync d'adopt exclut ceux du template) → CI/tests/code client effacés puis commités. Double protection : **mode `--brownfield`** (aucun strip, deletes de profil confinés à `.claude/`, permissions et inventaires non purgés — le SKILL adopt le passe désormais, et `render --check` repasse AVANT le cleanup) **+ sentinelles de propriété** (`_is_template_owned` : un `.github/`/`test/`/`plugins/` homonyme sans marqueur template n'est **jamais** supprimé, même sans flag).
- **🔴 `prune_dead_permissions` effaçait des allow-rules vivantes** : globs (`.claude/hooks/*.py`) testés en chemin littéral, chemins `~/.claude/…` matchés en substring → supprimés à tort. Lookbehind d'ancrage + skip des chemins à métacaractères ; au doute on **garde** (une règle morte est inoffensive, une vivante supprimée = prompts en boucle).
- **🔴 Deny `.env` troué** : l'énumération laissait `.env.prod`, `.env.dev`… **silencieusement lisibles** via l'allow `Read(./**)`. Ajout du filet **`ask: Read(./.env.*)`** — fail-closed : tout `.env.*` non listé en deny déclenche un prompt ; `.env.example` lisible après 1 confirmation.
- **Projet généré propre** : `prune_bootstrap_inventory` purge les lignes `/init-from-template` + `/adopt-template` des index shippés (`.claude/CLAUDE.md`, `template-maintenance.md`, `USAGE.md`) ; sections « Garantie skills vitaux » / « affiner ensuite » réécrites (le cleanup **s'auto-retire**, décision de type AVANT exécution) ; vérif post-init sans `render.py` (grep) ; note marketplace sans liens locaux morts.
- **Rsync brownfield aligné** (adopt SKILL + USAGE) : exclut `EXAMPLES/`, `plugins/`, `.claude-plugin/` comme le greenfield.
- **`render.py`** : EXCLUDE += `plugins/` + `.claude-plugin/` (les exemples `{{ }}` n8n des plugins ne sont pas des placeholders).
- **CI durcie** : garde SendMessage tolère l'absence de `tools:` (héritage complet = conforme) ; check manifests **croisé** (sources présentes, `plugins/*` tous recensés, `name` plugin ↔ marketplace) ; références `/n8n-push` mortes nettoyées (STRUCTURE.md, exemple ACME ×3) ; entrée `adopt-template` redondante retirée de `SCRIPT_JETABLE`.

### Added

- **`test/test_cleanup.py`** (40 asserts, stdlib) + step CI : greenfield strippé/pruné, **homonymes protégés**, **brownfield intouché**, dry-run inerte — les 2 fonctions destructrices ne re-régresseront plus en silence.

## [0.9.0] — 2026-07-06

Composants stack → **plugins** (archi C incrémentale) : les capacités optionnelles sortent du scaffold standalone pour devenir des plugins installables par projet, **auto-découverts** par le harness → plus aucun inventaire `.md` à maintenir pour eux.

### Added

- **Marketplace** dans le repo (`.claude-plugin/marketplace.json`) + 2 plugins sous `plugins/` : **`n8n-expertise`** (les 7 skills n8n) et **`db-migration`** (Alembic), chacun avec `.claude-plugin/plugin.json` (`skills: "./skills/"`) + README. Install par projet : `/plugin marketplace add kurt83340/claude-Setup` puis `claude plugin install <plugin>@claude-setup --scope project` (skills namespacés `/<plugin>:<skill>`).
- **Check CI** « manifestes marketplace + plugins valides ».

### Changed

- **`cleanup-for-type.py`** : `automation-n8n`/`bdd-migration` ne copient plus de skills (retrait `copy_examples`/`copy_examples_glob` + les 2 fonctions de copie devenues mortes) ; `plugins/` + `.claude-plugin/` ajoutés au strip des artefacts de maintenance (le projet **installe** depuis le marketplace, il n'embarque pas la source).
- **`EXAMPLES/skills-n8n/` + `EXAMPLES/skills-db/` supprimés** (déplacés dans `plugins/`) → `EXAMPLES/` ne garde que l'exemple ACME. Le rsync d'init exclut désormais `plugins/` + `.claude-plugin/`.
- Doc basculée « skills stack copiés depuis EXAMPLES » → « plugins » : init SKILL, `.claude/CLAUDE.md`, `.claude/skills/README.md`, `template-maintenance.md`, `STRUCTURE.md`, `USAGE.md`, README repo.

## [0.8.2] — 2026-07-06

### Added

- **Garde-fou CI « teammate → SendMessage »** — nouvelle étape CI + règle #4 dans `agents/README.md` : toute déf `.claude/agents/*.md` (hors subagent pur `doc-maintainer`) DOIT lister `SendMessage` dans `tools:`, sinon le build **échoue**. Empêche de recréer le bug v0.8.1 (teammate muet) en ajoutant un futur rôle — plus besoin d'y penser, l'oubli est attrapé automatiquement.

## [0.8.1] — 2026-07-06

### Fixed

- **Teammates muets : `SendMessage` absent des défs d'agents** — spawné **nommé**, un agent tourne en **teammate** (session à boîte aux lettres) et son texte final ne remonte PAS au lead : le seul canal est l'outil `SendMessage`. Or **aucune** déf `agents/*.md` ne le listait dans son `tools:` (bug révélé par les explorateurs de `/conception` spawnés nommés → rapport évaporé, idle muet, zombie qui ping). `SendMessage` ajouté aux **8 rôles teammate** (`worker`, `front-end`, `back-end`, `tester`, `reviewer`, `explore-code`, `explore-docs`, `explore-memoire`) + garde-fou dans `.claude/rules/agent-teams.md` (§ intro). `doc-maintainer` (subagent pur, jamais teammate) laissé tel quel.

## [0.8.0] — 2026-07-06

Hygiène d'init : un projet **généré** ne doit hériter d'**aucun** artefact de maintenance du template — sinon sa CI casse (elle teste des chemins que l'init supprime) et il traîne du cruft.

### Changed

- **`cleanup-for-type.py` retire les artefacts de maintenance DU template pour TOUS les types** (nouveau `TEMPLATE_MAINTENANCE` + `strip_template_maintenance`) : `.github/` (self-CI qui testait `render.py` / `EXAMPLES` / l'inventaire des skills → **CI rouge héritée**, la cause racine), `test/`, `EXAMPLES/` (après copie des skills stack) et les skills bootstrap `adopt-template` + `init-from-template` (retiré **en dernier** — il contient le script). Résultat : le projet généré démarre **propre, sans CI héritée**.
- **Suppression déplacée du shell vers Python** : le SKILL `init-from-template` ne fait plus de `rm -rf` / `git rm` à la main (Étape 4 = simple `git add -A` + commit) — tout passe par `shutil.rmtree` dans `cleanup-for-type.py`, donc plus jamais bloqué par la règle `deny Bash(rm -rf:*)` (source de refus + retries à chaque init).
- Nouveau `prune_dead_permissions` : purge de `settings.json` les allow-rules pointant vers un script `.claude/…` supprimé (ex. les 2 règles `init-from-template` render/cleanup, mortes une fois le skill bootstrap retiré).

### Fixed

- **`settings.json` : deny `Read(./.env.*)` trop large** — il bloquait aussi `.env.example` (fichier template sain, committé). Remplacé par un set énuméré (`.env`, `.env.local`, `.env.*.local`, `.env.{development,staging,production,test}`) : les vrais secrets restent bloqués, `.env.example` / `.sample` / `.template` redeviennent lisibles.

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
