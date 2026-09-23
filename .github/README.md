# claude-Setup

> Template **Claude Code** pour projets solo / client — Spec-Driven Development + « doc-as-memory » versionnée.
> Maintenu par [@kurt83340](https://github.com/kurt83340). Version courante : voir [`.claude/template-version`](../.claude/template-version) · [CHANGELOG](CHANGELOG.md).

Base standard pour démarrer un projet (automatisation n8n, app Python, web app, BDD, script) avec un contexte Claude Code propre dès la première session — **et le garder à jour** ensuite.

## Ce qu'il contient

- **Skills cœur** (`.claude/skills/` — inventaire canonique, compte vérifié par la CI → [`.claude/skills/README.md`](../.claude/skills/README.md)) : `/handoff`, `/spec`, `/conception`, `/feature` (pipelines), `/feature-done`, `/debug`, `/pivot`, `/archive-projet`, `/upgrade-template`, `/lecon`, `/adr`, `/idee`, `/doc-health`, `/codemap`, `/scaffold`, `/init-from-template`, `/adopt-template`.
- **Plugins** (marketplace `claude-setup`, dossier `plugins/`) : `db-migration`, `agent-teams` (**opt-in** : `/agent-teams:team` + rôles d'exécution + hook de trace — activé projet par projet au 1er lancement). Stack n8n = plugin officiel `n8n-mcp-skills` (czlonkowski/n8n-skills).
- **Agents cœur** : `explore-code` / `explore-docs` / `explore-memoire` (explorateurs lecture seule), `reviewer` (revue adverse), `doc-maintainer` (maintenance doc en lot — jamais le HANDOFF).
- **Hooks** : filet « n'oublie rien » (snapshot si une session se ferme SANS `/handoff` après avoir modifié le dépôt, réinjecté au démarrage suivant), snapshot pré-compaction, gotchas ciblés injectés à l'édition du fichier concerné, rappel `/handoff` (1×/session), garde-fous de budget de contexte, growth-detection.
- **Doc structurée** : cadrage / conception (PRD, ARCHITECTURE) / specs / ADR / ROADMAP / HANDOFF / code-map / stack…
- **Budget de contexte tenu** : `CLAUDE.md` = index just-in-time (2 `@-imports` bornés) ; ~6,5k tokens auto-chargés au démarrage sur le template vierge (mesure `context-budget.py`, seuil CI 8k) ; rules scopées par chemin.
- **Garde-fous secrets** : `.env*` ignorés à toute profondeur, lecture refusée par `settings.json`, gitleaks en pre-commit (`.pre-commit-config.yaml`).

## Démarrer un projet

```bash
rsync -av --exclude='EXAMPLES/' --exclude='test/' --exclude='.github/' --exclude='.git/' \
  --exclude='plugins/' --exclude='.claude-plugin/' \
  ./ /chemin/vers/mon-projet/
cd /chemin/vers/mon-projet
claude   # puis, dans la session : /init-from-template
# garde-fou secrets (une fois par clone) : pre-commit install
```

**Projet existant (brownfield)** : même rsync avec `--ignore-existing` (+ exclure `README.md` et
`.env.example`), puis `/adopt-template` — merges non destructifs + rétro-remplissage de la doc
depuis l'existant. Détails : [USAGE.md § Projet EXISTANT](../.claude/USAGE.md).

## Mettre à jour un projet déjà généré

Les fichiers de **méthode** (hooks, skills, agents, rules, settings, index `CLAUDE.md`) se mettent à
jour par **merge 3 voies** : ce que le projet n'a pas touché prend la nouvelle version, ses
personnalisations sont gardées, les conflits sont signalés (jamais écrasés). La doc projet
(`.claude/docs/`) n'est modifiée que par des migrations versionnées (ex. < 1.4.0 : journal HANDOFF et
gotchas sortis des fichiers auto-chargés).

- Projet ≥ 1.5.0 : `/upgrade-template` (dry-run montré, validation, application, conflits guidés, commit).
- Projet plus ancien (le skill n'existe pas encore chez lui) — depuis sa racine, arbre git propre :

```bash
git clone --quiet https://github.com/kurt83340/claude-Setup /tmp/claude-setup
python3 /tmp/claude-setup/.claude/skills/upgrade-template/scripts/upgrade.py --project . --template /tmp/claude-setup --dry-run
python3 /tmp/claude-setup/.claude/skills/upgrade-template/scripts/upgrade.py --project . --template /tmp/claude-setup
```

Testé sur les 17 versions taguées (v0.16.0 → v1.4.1) : un projet non modifié devient octet pour octet
une init fraîche de la dernière version.

## Maintenance du template

- Tests mécaniques (rejoués en CI à chaque push) : `test/test_hooks.py` · `test_render.py` ·
  `test_cleanup.py` · `test_skills.py` · `test_archive.py` · `test_context_budget.py` ·
  `test_upgrade.py` (toutes les versions taguées → version courante) · `phase0-harness.py` (init
  réelle × 6 profils) · `sim-growth.py` (projets qui grossissent session après session : budget,
  filet, upgrade à mi-vie)
- Vérification **live** des hooks dans de vraies sessions `claude -p` (manuelle, quelques appels
  haiku) : `python3 test/live-hooks-check.py` — à rejouer à chaque montée de Claude Code
- Test agentique : [test/PROTOCOL-E2E.md](../test/PROTOCOL-E2E.md) + `python3 test/verify-e2e.py --root <jetable>`
- **Publier une version** : bump `.claude/template-version` + entrée en tête de [CHANGELOG.md](CHANGELOG.md)
  (la CI vérifie l'égalité) → push sur `main` : la CI crée le tag `vX.Y.Z` (base de merge de
  `/upgrade-template` — sans tag, les projets de cette version se mettent à jour en mode prudent).
  Plugin modifié → bump de la `version` de son `plugin.json`.

## Licence

Usage personnel pour l'instant. Le dépôt est public : ajouter une `LICENSE` avant toute diffusion.
