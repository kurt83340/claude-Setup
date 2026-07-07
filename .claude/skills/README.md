# `.claude/skills/` — Organisation

> Skills perso et importés depuis d'autres sources, **à plat** dans ce dossier.

## Convention

```
.claude/skills/
├── <skill-1>/SKILL.md     # invocable via /<skill-1>
├── <skill-2>/SKILL.md     # invocable via /<skill-2>
└── ...
```

**Pas de sous-dossier de regroupement.** Claude Code scanne `.claude/skills/<nom>/SKILL.md` à **1 niveau seulement** (cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192) — feature request OPEN pour discovery récursive).

## Règles

1. **Le `name:` du frontmatter doit matcher le nom du dossier.**
   Ex : `.claude/skills/handoff/SKILL.md` avec `name: handoff` → invoque `/handoff`.

2. **Tout est dans le même espace de noms** (`.claude/skills/`, `~/.claude/skills/`, plugins). Si collision → Claude en utilise un (alphabétique). Rename le dossier + `name:` du moins prioritaire.

3. **Pour grouper des skills par thème, 2 options :**
   - **Préfixe le nom** : `n8n-deploy`, `n8n-test`, `n8n-lint` (simple, usage perso)
   - **Package en plugin** : `<plugin>/skills/<skill>/SKILL.md` → invocation `/<plugin>:<skill>` (officiel, namespacing préservé)

## Importer un skill externe

### Depuis GitHub

```bash
# Cloner dans un dossier temp
git clone <repo-url> /tmp/external-skills

# Copier chaque SKILL.md directement sous .claude/skills/
# (en préfixant le nom si tu veux marquer la provenance)
cp -r /tmp/external-skills/skills/foo .claude/skills/n8n-foo
# → édite SKILL.md pour aligner name: n8n-foo
```

### Depuis un MCP server

Les MCP servers exposent des "tools" automatiquement (sans SKILL.md). Pour wrapper un MCP tool comme skill invocable :

```bash
mkdir -p .claude/skills/mcp-<tool>
cat > .claude/skills/mcp-<tool>/SKILL.md <<'EOF'
---
name: mcp-<tool>
description: Wrapper pour le MCP tool X (server Y)
allowed-tools: mcp__<server>__<tool>
---

# Invocation du MCP tool <tool>
...
EOF
```

### Depuis un plugin Claude Code

Les plugins ont leur propre namespace automatiquement (`plugin-name:skill-name`). Pas besoin de copier dans `.claude/skills/` — l'invocation devient `/<plugin>:<skill>`.

## Skills du template (à plat)

| Skill                 | Quoi                                            |
| --------------------- | ----------------------------------------------- |
| `/handoff`            | Snapshot .claude/docs/HANDOFF.md fin de session |
| `/spec`               | Scaffold nouvelle feature                       |
| `/feature-done`       | Marque feature comme livrée                     |
| `/pivot`              | Workflow pivot client 9 étapes                  |
| `/lecon`              | Cycle de vie leçons                             |
| `/adr`                | Cycle de vie ADR                                |
| `/idee`               | Cycle de vie idées                              |
| `/doc-health`         | Audit hebdo doc                                 |
| `/codemap`            | Régénère .claude/docs/code-map.md               |
| `/init-from-template` | Init projet depuis ce template (UNE FOIS)       |

## Skills stack-spécifiques = PLUGINS (marketplace `claude-setup`, dossier `plugins/`)

Pas livrés dans `.claude/skills/` — packagés en **plugins** installés par projet via `/plugin`
(auto-découverts, aucun inventaire à maintenir). Recensés ici pour visibilité.

| Plugin          | Skills                 | Install (selon type projet)                                     |
| --------------- | ---------------------- | --------------------------------------------------------------- |
| `n8n-expertise` | 7 skills n8n (`n8n-*`) | `automation-n8n` → `/plugin install n8n-expertise@claude-setup` |
| `db-migration`  | `db-migration`         | `bdd-migration` → `/plugin install db-migration@claude-setup`   |

## Skills built-in Claude Code (hors `.claude/skills/`)

Disponibles automatiquement : `/security-review`, `/code-review`, `/init`, `/resume`, `/compact`, `/doctor`. Pas besoin de SKILL.md.
