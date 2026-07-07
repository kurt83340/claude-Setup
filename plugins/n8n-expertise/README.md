# Plugin `n8n-expertise`

> **7 skills d'expertise n8n** (référence), packagés en **plugin Claude Code** installable par projet.
> Fait partie du marketplace `claude-setup` (racine du repo : [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)).

| Skill | Invocation | Quoi |
| --- | --- | --- |
| [n8n-node-configuration](skills/n8n-node-configuration/SKILL.md) | `/n8n-expertise:n8n-node-configuration` | Config des nœuds selon l'opération : dépendances de propriétés, champs requis, patterns par type |
| [n8n-validation-expert](skills/n8n-validation-expert/SKILL.md) | `/n8n-expertise:n8n-validation-expert` | Interpréter/corriger les erreurs & warnings de validation (faux positifs, profils, boucle) |
| [n8n-workflow-patterns](skills/n8n-workflow-patterns/SKILL.md) | `/n8n-expertise:n8n-workflow-patterns` | Patterns d'architecture éprouvés : webhook, HTTP/API, DB, AI agent, batch |
| [n8n-code-javascript](skills/n8n-code-javascript/SKILL.md) | `/n8n-expertise:n8n-code-javascript` | JavaScript dans les Code nodes (`$input`/`$json`/`$node`, `$helpers`, DateTime) |
| [n8n-code-python](skills/n8n-code-python/SKILL.md) | `/n8n-expertise:n8n-code-python` | Python dans les Code nodes (`_input`/`_json`, stdlib, limites) |
| [n8n-expression-syntax](skills/n8n-expression-syntax/SKILL.md) | `/n8n-expertise:n8n-expression-syntax` | Syntaxe des expressions `{{ }}`, erreurs courantes, mapping entre nœuds |
| [n8n-mcp-tools-expert](skills/n8n-mcp-tools-expert/SKILL.md) | `/n8n-expertise:n8n-mcp-tools-expert` | Outils MCP `n8n-mcp` (search nodes, validation, templates, workflows/credentials, audit) |

Skills **auto-découverts** par le harness (aucun listing `.claude/CLAUDE.md` requis) et **auto-invoqués** par leur `description` quand le contexte s'y prête. Namespacés `/<plugin>:<skill>`.

## Installer (dans un projet)

```bash
# 1. Ajouter le marketplace (une fois) depuis le repo template
/plugin marketplace add kurt83340/claude-Setup
# 2. Installer le plugin, scope projet (versionné dans .claude/settings.json → partagé équipe)
claude plugin install n8n-expertise@claude-setup --scope project
```

Désinstaller : `/plugin uninstall n8n-expertise@claude-setup --scope project`. Désactiver sans supprimer : `/plugin disable n8n-expertise@claude-setup` (+ `/reload-plugins`).

## Ajouter / modifier un skill

Dépose `skills/n8n-<nom>/SKILL.md` ici. Il est auto-découvert (le champ `skills: "./skills/"` du [`plugin.json`](.claude-plugin/plugin.json) pointe le dossier). Bump `version` du plugin + du marketplace pour propager l'update aux projets (`/plugin marketplace update claude-setup`).
