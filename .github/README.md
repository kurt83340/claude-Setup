# claude-Setup

> Template **Claude Code** pour projets solo / client — Spec-Driven Development + « doc-as-memory » versionnée.
> Maintenu par [@kurt83340](https://github.com/kurt83340). Audité & corrigé le 2026-06-28.

Base standard pour démarrer un projet (automatisation n8n, app Python, BDD, mini-app) avec un contexte Claude Code propre dès la première session.

## Ce qu'il contient

- **12 skills cœur** (`.claude/skills/`) : `/handoff`, `/spec`, `/conception`, `/feature-done`, `/team`, `/adr`, `/lecon`, `/idee`, `/doc-health`, `/codemap`, `/pivot`, `/init-from-template` — + skills **stack** (hors-cœur, dans `EXAMPLES/skills-*`) : n8n (×3), `db-migration`. Inventaire canonique → `.claude/CLAUDE.md`.
- **Agents** : `doc-maintainer` (subagent, maintenance doc en batch) + rôles teammate agent-teams — `worker`, `front-end`, `back-end`, `tester`, `reviewer` — + 3 explorateurs lecture seule `explore-code`/`explore-docs`/`explore-memoire` pour `/conception` (protocole : `.claude/rules/agent-teams.md`)
- **Agent teams câblés** : flag + `teammateMode: "tmux"` dans `settings.json` (teammates visibles en split panes), orchestration `/team`, débrief mémoire des rapports
- **Hooks** lifecycle : snapshots pré-compaction **et** fin de session (filet « n'oublie rien ») → `.claude/.cache/`, ré-injections, code-map, growth-detection, rappel `/handoff`, trace d'équipe
- **Doc structurée** : cadrage / conception (PRD, ARCHITECTURE, specs) / ADR / ROADMAP / HANDOFF / code-map / stack…
- **`CLAUDE.md` en index just-in-time** : ~1,5k tokens auto-chargés (vs ~14,6k si on charge tout)

## Démarrer un projet

```bash
rsync -av --exclude='EXAMPLES/acme-sync-erp-notion-docs/' --exclude='test/' --exclude='.github/' --exclude='.git/' \
  ./ /chemin/vers/mon-projet/
cd /chemin/vers/mon-projet
chmod +x .claude/hooks/*.py .claude/hooks/*.sh
claude   # puis, dans la session : /init-from-template
```

> `EXAMPLES/skills-*` (n8n, db-migration) est **conservé** : `/init-from-template` y copie les skills stack selon le type de projet. Seul l'exemple ACME est exclu. Tu peux retirer `EXAMPLES/` à la fin si tu n'en as plus besoin.

→ Guide complet : **[USAGE.md](../USAGE.md)** · Convention : **[STRUCTURE.md](../STRUCTURE.md)** · Exemple rempli : **[EXAMPLES/](../EXAMPLES/)**

## Maintenance du template

- Audit & décisions vérifiées : [test/AUDIT-2026-06-28.md](../test/AUDIT-2026-06-28.md)
- Tests des hooks : `python3 test/test_hooks.py` · tests init : `python3 test/test_render.py` (rejoués en CI à chaque push)
- Packaging plugin (proto) : `python3 test/build-plugin.py --out dist`
- Historique des versions : [CHANGELOG.md](CHANGELOG.md)

## Licence

Usage personnel pour l'instant. Ajouter une `LICENSE` avant toute diffusion publique.
