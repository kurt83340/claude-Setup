# Plugin `agent-teams`

> **Exécution d'équipe** du template claude-Setup, packagée en plugin Claude Code installable par projet.
> Marketplace `claude-setup` (racine du repo : [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)).

| Composant | Quoi |
| --- | --- |
| Skill [`team`](skills/team/SKILL.md) → **`/agent-teams:team <spec-id>`** | Orchestre une équipe de teammates tmux : plan validé, 1 worktree/codeur, task list native, TDD opt-in, suivi, merge, débrief mémoire, clôture |
| Agents [`worker`](agents/worker.md) · [`front-end`](agents/front-end.md) · [`back-end`](agents/back-end.md) · [`tester`](agents/tester.md) | **Rôles d'exécution** teammate (généraliste, UI, serveur, QA) — auto-découverts à l'installation |
| Hook [`teamtask-log.py`](hooks/teamtask-log.py) (TaskCreated/TaskCompleted/TeammateIdle) | Trace JSON de progression d'équipe → `.claude/.cache/team-progress.log` |

## Ce qui reste dans le CŒUR du template (dépendances des skills cœur)

- **`reviewer`** (revue adverse de `/conception` + review d'équipe) et les **explorateurs** `explore-code`/`explore-docs`/`explore-memoire` → `.claude/agents/`
- La **rule [`agent-teams.md`](../../.claude/rules/agent-teams.md)** (protocole lead/teammate, SOURCE UNIQUE — auto-chargée, valable plugin installé ou pas)
- Le câblage `settings.json` : `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` + `teammateMode: "tmux"` (inertes sans le plugin)

## Installer (dans un projet)

```bash
/plugin marketplace add kurt83340/claude-Setup          # une fois
claude plugin install agent-teams@claude-setup --scope project
```

Prérequis : `tmux` dans le PATH (sinon `teammateMode` retombe en in-process).
Désinstaller : `/plugin uninstall agent-teams@claude-setup --scope project`.

> 🧑‍🤝‍🧑 Un projet **solo/n8n** n'a pas besoin de ce plugin — c'est précisément pourquoi il est sorti du cœur.
