# claude-Setup

> Template **Claude Code** pour projets solo / client — Spec-Driven Development + « doc-as-memory » versionnée.
> Maintenu par [@kurt83340](https://github.com/kurt83340). Audité & corrigé le 2026-06-28.

Base standard pour démarrer un projet (automatisation n8n, app Python, BDD, mini-app) avec un contexte Claude Code propre dès la première session.

## Ce qu'il contient

- **11 skills** (`.claude/skills/`) : `/handoff`, `/spec`, `/feature-done`, `/adr`, `/lecon`, `/idee`, `/doc-health`, `/codemap`, `/pivot`, `/db-migration`, `/init-from-template`
- **1 agent** `doc-maintainer` (maintenance doc en batch, diff par diff)
- **5 hooks** lifecycle : snapshot pré-compaction → `.claude/.cache/`, ré-injection, code-map, growth-detection, rappel `/handoff`
- **Doc structurée** : cadrage / conception (PRD, ARCHITECTURE, specs) / ADR / ROADMAP / HANDOFF / code-map / stack…
- **`CLAUDE.md` en index just-in-time** : ~1,5k tokens auto-chargés (vs ~14,6k si on charge tout)

## Démarrer un projet

```bash
rsync -av --exclude='EXAMPLES/' --exclude='test/' --exclude='.github/' --exclude='.git/' \
  ./ /chemin/vers/mon-projet/
cd /chemin/vers/mon-projet
chmod +x .claude/hooks/*.py .claude/hooks/*.sh
claude   # puis, dans la session : /init-from-template
```

→ Guide complet : **[USAGE.md](../USAGE.md)** · Convention : **[STRUCTURE.md](../STRUCTURE.md)** · Exemple rempli : **[EXAMPLES/](../EXAMPLES/)**

## Maintenance du template

- Audit & décisions vérifiées : [test/AUDIT-2026-06-28.md](../test/AUDIT-2026-06-28.md)
- Tests des hooks : `python3 test/test_hooks.py` (rejoué en CI à chaque push)
- Packaging plugin (proto) : `python3 test/build-plugin.py --out dist`
- Historique des versions : [CHANGELOG.md](CHANGELOG.md)

## Licence

Usage personnel pour l'instant. Ajouter une `LICENSE` avant toute diffusion publique.
