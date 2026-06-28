# `EXAMPLES/skills-n8n/` — Skills exemples pour stack n8n

> 3 skills typiques d'un projet d'automatisation n8n, à copier dans `.claude/skills/` et adapter.
> Préfixe `n8n-` = convention de groupement (les skills sont à plat, 1 niveau — cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192)).

| Skill | Invocation | Quoi |
| --- | --- | --- |
| [n8n-push/](n8n-push/SKILL.md) | `/n8n-push` | Publie le workflow sur le tenant |
| [n8n-seed-db/](n8n-seed-db/SKILL.md) | `/n8n-seed-db` | Génère les fixtures de test |
| [n8n-deploy/](n8n-deploy/SKILL.md) | `/n8n-deploy` | Pipeline complet (tests + migration + push) — `disable-model-invocation: true` |

## Installation

Copié automatiquement par `/init-from-template` (type `automation-n8n`), ou à la main :

```bash
cp -r EXAMPLES/skills-n8n/n8n-* .claude/skills/
```

**Le nom d'invocation = le nom du dossier** (`.claude/skills/n8n-push/SKILL.md` → `/n8n-push`).
Le `name:` du frontmatter n'est qu'un label d'affichage.

## Rappels format skill

- `description:` dans le frontmatter → Claude peut **invoquer le skill automatiquement** quand pertinent.
  Pour un skill sensible (deploy !), mettre `disable-model-invocation: true` → slash-only.
- Fichiers de support possibles dans le dossier du skill (`templates/`, `scripts/`…) — c'est l'avantage du format.
- Après ajout/modif : pris en compte à chaud (ou `/reload-skills`).

> ℹ️ Historique : ces exemples étaient auparavant des « custom commands » (`.claude/commands/*.md`).
> Les commands et skills ont **fusionné** (même moteur) et la doc officielle recommande les skills —
> le template n'utilise plus que le format skill. Source : [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).
