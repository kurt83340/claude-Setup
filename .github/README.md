# claude-Setup

> Template **Claude Code** pour projets solo / client — Spec-Driven Development + « doc-as-memory » versionnée.
> Maintenu par [@kurt83340](https://github.com/kurt83340). Audité & corrigé le 2026-06-28.

Base standard pour démarrer un projet (automatisation n8n, app Python, BDD, mini-app) avec un contexte Claude Code propre dès la première session.

## Ce qu'il contient

- **Skills cœur** (`.claude/skills/` — inventaire canonique **et compte CI-vérifié** → `.claude/CLAUDE.md`) : `/handoff`, `/spec`, `/conception`, `/feature` (pipelines), `/feature-done`, `/debug`, `/scaffold`, `/adr`, `/lecon`, `/idee`, `/doc-health`, `/codemap`, `/pivot`, `/init-from-template`, `/adopt-template` — + **plugins stack** (marketplace `claude-setup`, dossier `plugins/`) : `db-migration`, `agent-teams` (`/team` + rôles d'exécution + hook) — stack n8n = plugin officiel `n8n-mcp-skills` (czlonkowski/n8n-skills). Inventaire cœur → `.claude/CLAUDE.md`.
- **Agents cœur** : `doc-maintainer` (subagent, maintenance doc en batch) + `reviewer` (revue adverse lecture seule) + 3 explorateurs `explore-code`/`explore-docs`/`explore-memoire` pour `/conception` — les rôles d'exécution (`worker`, `front-end`, `back-end`, `tester`) viennent du plugin `agent-teams` (protocole : `.claude/rules/agent-teams.md`)
- **Agent teams câblés** : flag + `teammateMode: "tmux"` dans `settings.json` (teammates visibles en split panes), orchestration `/agent-teams:team` (plugin), débrief mémoire des rapports
- **Hooks** lifecycle : snapshots pré-compaction **et** fin de session (filet « n'oublie rien ») → `.claude/.cache/`, ré-injections, code-map, growth-detection, rappel `/handoff`, trace d'équipe
- **Doc structurée** : cadrage / conception (PRD, ARCHITECTURE, specs) / ADR / ROADMAP / HANDOFF / code-map / stack…
- **`CLAUDE.md` en index just-in-time** : ~1,5k tokens auto-chargés (vs ~14,6k si on charge tout)

## Démarrer un projet

```bash
rsync -av --exclude='EXAMPLES/' --exclude='test/' --exclude='.github/' --exclude='.git/' \
  --exclude='plugins/' --exclude='.claude-plugin/' \
  ./ /chemin/vers/mon-projet/
cd /chemin/vers/mon-projet
chmod +x .claude/hooks/*.py .claude/hooks/*.sh
claude   # puis, dans la session : /init-from-template
# Stack n8n ? plugin officiel : /plugin marketplace add czlonkowski/n8n-skills ; /plugin install n8n-mcp-skills@n8n-mcp-skills
```

**Projet existant (brownfield)** : même rsync avec `--ignore-existing` (+ exclure `README.md`
et `.env.example`), puis `/adopt-template` — merges non-destructifs + rétro-remplissage de la
doc depuis l'existant. Détails : [USAGE.md § Projet EXISTANT](../.claude/USAGE.md).

> Les **plugins maison** (`db-migration`, `agent-teams`) vivent dans `plugins/` (marketplace `claude-setup`) ; la stack **n8n** = plugin **officiel** [`n8n-mcp-skills`](https://github.com/czlonkowski/n8n-skills) (14 skills + hooks, czlonkowski). Un projet **installe** via `/plugin`, il n'embarque rien (le rsync exclut `plugins/` + `.claude-plugin/` ; ACME aussi).

→ Guide complet : **[USAGE.md](../.claude/USAGE.md)** · Convention : **[STRUCTURE.md](../.claude/STRUCTURE.md)** · Exemple rempli : **[EXAMPLES/](../EXAMPLES/)**

## Maintenance du template

- Audit & décisions vérifiées : [test/AUDIT-2026-06-28.md](../test/AUDIT-2026-06-28.md)
- Tests mécaniques : `python3 test/test_hooks.py` · `test_render.py` · `test_cleanup.py` · `test_skills.py` (rejoués en CI à chaque push)
- **Test agentique** : [test/PROTOCOL-E2E.md](../test/PROTOCOL-E2E.md) (13 phases sur projet jetable — dont Phase B : scénarios comportementaux [test/benchmarks/](../test/benchmarks/) — à rejouer à chaque version majeure) + `python3 test/verify-e2e.py --root <jetable>` (invariants post-run)
- Historique des versions : [CHANGELOG.md](CHANGELOG.md)

## Licence

Usage personnel pour l'instant. Ajouter une `LICENSE` avant toute diffusion publique.
