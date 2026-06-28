# Changelog — template claude-Setup

Format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versions [SemVer](https://semver.org/lang/fr/).
Versions du **template lui-même** — distinct du CHANGELOG d'un projet généré (qui vit dans `.claude/docs/CHANGELOG.md`).

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
