# Changelog — template claude-Setup

Format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versions [SemVer](https://semver.org/lang/fr/).
Versions du **template lui-même** — distinct du CHANGELOG d'un projet généré (qui vit dans `.claude/docs/CHANGELOG.md`).

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
