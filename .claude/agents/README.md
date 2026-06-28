# `.claude/agents/` — Organisation

> Custom agents (sous-agents Claude spécialisés), **à plat** dans ce dossier.

## Convention

```
.claude/agents/
├── <agent-1>.md
├── <agent-2>.md
└── ...
```

**Pas de sous-dossier de regroupement.** Claude Code scanne `.claude/agents/<nom>.md` à **1 niveau** (même limitation que skills, cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192)).

## Règles

1. **L'identifier vient du frontmatter `name:`** (qui doit matcher le nom du fichier).
   Ex : `.claude/agents/doc-maintainer.md` avec `name: doc-maintainer` → invoquable via Task tool avec `subagent_type: doc-maintainer`.

2. **Frontmatter requis** : `name`, `description`, `tools`, `model: inherit` (ou model ID).

3. **Tout est dans le même espace de noms** — pas de collision possible avec namespacing par sous-dossier.

## Invocation

Les agents sont invoqués via le **Task tool** (pas en slash `/agent-name`) :

```
Lance l'agent doc-maintainer pour faire un audit complet du projet
```

Claude utilisera automatiquement le Task tool avec `subagent_type: doc-maintainer`.

## Importer un agent externe

```bash
# Copier directement le .md dans .claude/agents/
cp <source>/agent.md .claude/agents/<agent-name>.md
# Si tu veux marquer la provenance → préfixer le nom : n8n-expert.md, etc.
```

## Limitations agents importés depuis plugins

Plugin agents ne supportent PAS les frontmatter fields : `hooks`, `mcpServers`, `permissionMode` (ignorés silencieusement). Pour ces fields → copier le `.md` localement dans `.claude/agents/`.

## Agents du template

| Agent              | Quoi                                                                      |
| ------------------ | ------------------------------------------------------------------------- |
| `doc-maintainer`   | Maintient HANDOFF, ROADMAP, CHANGELOG, ADRs, pivots, archivage. Diff par diff. |
