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

4. **Rôle teammate → `SendMessage` OBLIGATOIRE dans `tools:`** (tout agent, sauf subagent pur type `doc-maintainer`). Spawné **nommé**, un agent tourne en teammate et ne peut rapporter au lead QUE via `SendMessage` — sans lui : rapport perdu, idle muet, zombie qui ping. **Vérifié en CI** (étape « Défs teammate — SendMessage »), donc pas besoin d'y penser : l'oubli fait échouer le build. Détail : [agent-teams.md](../rules/agent-teams.md).

## Invocation — subagent OU teammate

Un même fichier `.claude/agents/*.md` s'invoque de **deux façons** (jamais en slash `/agent-name`) :

1. **Subagent (Task tool)** — headless, invisible, one-shot ; le résultat revient comme
   retour d'outil. Ex : `Lance l'agent doc-maintainer pour un audit complet`.
2. **Teammate (agent teams)** — session Claude Code complète, **visible en tmux**
   (`teammateMode: "tmux"` câblé dans `settings.json`), spawnée par le lead à partir de la
   définition d'agent (tools + model honorés, body ajouté au system prompt). C'est le mode
   des rôles d'équipe — en général via `/agent-teams:team` (plugin `agent-teams`).

Quand choisir quoi + protocole d'équipe (périmètre, cycle de vie, topologie) :
**source unique** [.claude/rules/agent-teams.md](../rules/agent-teams.md).

## Importer un agent externe

```bash
# Copier directement le .md dans .claude/agents/
cp <source>/agent.md .claude/agents/<agent-name>.md
# Si tu veux marquer la provenance → préfixer le nom : n8n-expert.md, etc.
```

## Limitations agents importés depuis plugins

Plugin agents ne supportent PAS les frontmatter fields : `hooks`, `mcpServers`, `permissionMode` (ignorés silencieusement). Pour ces fields → copier le `.md` localement dans `.claude/agents/`.

## Agents du template

| Agent             | Quoi                                                                           | Mode typique                         |
| ----------------- | ------------------------------------------------------------------------------ | ------------------------------------ |
| `doc-maintainer`  | Maintient HANDOFF, ROADMAP, CHANGELOG, ADRs, pivots, archivage. Diff par diff. | Subagent (Task)                      |
| `reviewer`        | Review **lecture seule** — diffs ET plans (`/conception`), findings 🔴/🟠/🟢   | Subagent ou teammate                 |
| `explore-code`    | Explorateur code (lecture seule) — patterns/intégration en `chemin:ligne`      | Subagent ou teammate (`/conception`) |
| `explore-docs`    | Explorateur docs externes — context7 → MCP → web, URLs + versions              | Subagent ou teammate (`/conception`) |
| `explore-memoire` | Explorateur mémoire projet — ADRs/leçons/idées : « déjà décidé/tenté ? »       | Subagent ou teammate (`/conception`) |

Les rôles portent chacun UNIQUEMENT leur spécialité ; le protocole d'équipe
(communication, périmètre, cycle de vie, topologie) vit dans la **rule**
[.claude/rules/agent-teams.md](../rules/agent-teams.md) — pas de duplication ici.

> 🧩 Les **rôles d'exécution** (`worker` · `front-end` · `back-end` · `tester`) +
> `/agent-teams:team` + le hook de trace vivent dans le **plugin `agent-teams`**
> (`/plugin install agent-teams@claude-setup`) — auto-découverts à l'installation.
