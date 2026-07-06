# `EXAMPLES/skills-n8n/` — Skills d'expertise n8n (stack)

> **7 skills d'expertise n8n** (référence : configuration de nœuds, validation, patterns,
> code, expressions, outils MCP), à copier dans `.claude/skills/` pour un projet d'automatisation n8n.
> Préfixe `n8n-` = convention de groupement (les skills sont à plat, 1 niveau — cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192)).

| Skill | Invocation | Quoi |
| --- | --- | --- |
| [n8n-node-configuration/](n8n-node-configuration/SKILL.md) | `/n8n-node-configuration` | Configuration des nœuds selon l'opération : dépendances de propriétés, champs requis, patterns par type de nœud |
| [n8n-validation-expert/](n8n-validation-expert/SKILL.md) | `/n8n-validation-expert` | Interpréter et corriger les erreurs/warnings de validation (faux positifs, profils, boucle de validation) |
| [n8n-workflow-patterns/](n8n-workflow-patterns/SKILL.md) | `/n8n-workflow-patterns` | Patterns d'architecture éprouvés : webhook, intégration HTTP/API, opérations DB, workflows AI agent, batch |
| [n8n-code-javascript/](n8n-code-javascript/SKILL.md) | `/n8n-code-javascript` | Écrire du JavaScript dans les Code nodes (`$input`/`$json`/`$node`, `$helpers`, DateTime, modes du Code node) |
| [n8n-code-python/](n8n-code-python/SKILL.md) | `/n8n-code-python` | Écrire du Python dans les Code nodes (`_input`/`_json`, stdlib, limites de Python dans n8n) |
| [n8n-expression-syntax/](n8n-expression-syntax/SKILL.md) | `/n8n-expression-syntax` | Valider la syntaxe des expressions n8n `{{ }}` et corriger les erreurs courantes (mapping entre nœuds, données webhook) |
| [n8n-mcp-tools-expert/](n8n-mcp-tools-expert/SKILL.md) | `/n8n-mcp-tools-expert` | Utiliser efficacement les outils MCP `n8n-mcp` (search nodes, validation, templates, gestion workflows/credentials, audit) |

> Ce sont des skills de **référence auto-invoqués** : leur `description` (`Use when…`) laisse Claude
> les déclencher tout seul quand le contexte s'y prête (configurer un nœud, écrire une expression, etc.).
> Chaque dossier embarque ses fichiers de support (`DEPENDENCIES.md`, `OPERATION_PATTERNS.md`, …) — l'avantage du format skill.

## Installation

Copié automatiquement par `/init-from-template` (type `automation-n8n`) — via un **glob** `n8n-*`
dans `cleanup-for-type.py` (donc ajouter/retirer un skill ici ne demande **aucune** modif du script). À la main :

```bash
cp -r EXAMPLES/skills-n8n/n8n-* .claude/skills/
```

**Le nom d'invocation = le nom du dossier** (`.claude/skills/n8n-code-python/SKILL.md` → `/n8n-code-python`).
Le `name:` du frontmatter n'est qu'un label d'affichage.

## Ajouter / mettre à jour un skill n8n

- Dépose le dossier `n8n-<nom>/` ici (avec son `SKILL.md`). Il sera copié au prochain `/init-from-template` type `automation-n8n` (glob), et recensé dans l'inventaire → [`.claude/CLAUDE.md`](../../.claude/CLAUDE.md).
- Pour un skill **sensible** (déploiement, push prod…), mets `disable-model-invocation: true` dans le frontmatter → invocation slash-only, jamais déclenché automatiquement par Claude.
- Après ajout/modif : pris en compte à chaud (ou `/reload-skills`).

> ℹ️ Ces skills vivent **hors du cœur** du template : ils ne sont pas dans `.claude/skills/` par défaut
> (donc pas soumis au check CI d'inventaire des skills cœur), mais copiés à la demande selon le type de projet.
