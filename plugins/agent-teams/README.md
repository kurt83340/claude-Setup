# Plugin `agent-teams`

> **Exécution d'équipe** du template claude-Setup, packagée en plugin Claude Code installable par projet.
> Marketplace `claude-setup` (racine du repo : [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)).

| Composant | Quoi |
| --- | --- |
| Skill [`team`](skills/team/SKILL.md) → **`/agent-teams:team <spec-id>`** | Orchestre une équipe de teammates tmux : plan validé, 1 worktree/codeur, task list native, TDD opt-in, suivi, merge, débrief mémoire, clôture |
| Agents [`worker`](agents/worker.md) · [`front-end`](agents/front-end.md) · [`back-end`](agents/back-end.md) · [`tester`](agents/tester.md) | **Rôles d'exécution** teammate (généraliste, UI, serveur, QA) — auto-découverts à l'installation |
| Hook [`teamtask-log.py`](hooks/teamtask-log.py) (TaskCreated/TaskCompleted/TeammateIdle) | Trace JSON de progression d'équipe → `.claude/.cache/team-progress.log` |

## Opt-in : rien dans le cœur tant que l'équipe n'est pas activée (v1.5.0)

Le cœur du template ne câble PLUS les agent teams : le flag `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
n'est pas inerte (d'après la doc, il monte une équipe à chaque session et laisse Claude proposer des
teammates), et la rule d'équipe pesait ~1,8k tokens sur chaque session de chaque projet — même solo.

- **Activation** = 1er lancement de `/agent-teams:team` : copie la rule
  [`skills/team/agent-teams-rule.md`](skills/team/agent-teams-rule.md) → `.claude/rules/agent-teams.md`
  (invariants lead/teammate, auto-chargée par chaque session du projet), pose
  `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "auto"` dans les settings du projet,
  puis demande une relance (flag lu au démarrage).
- Protocole complet : [`skills/team/protocole.md`](skills/team/protocole.md) (lu par `/agent-teams:team`).
- Restent dans le **cœur** (dépendances des skills cœur) : `reviewer` et les explorateurs
  `explore-code` / `explore-docs` / `explore-memoire` (`.claude/agents/`), utilisables en subagents sans équipe.

## Installer (dans un projet)

```bash
/plugin marketplace add kurt83340/claude-Setup          # une fois
claude plugin install agent-teams@claude-setup --scope project
# puis, dans Claude Code : /agent-teams:team <spec-id>   → activation au 1er lancement
```

Affichage : `teammateMode: "auto"` = un pane tmux par teammate si la session tourne DANS tmux
(`tmux new -s <projet>` avant `claude`), sinon teammates dans le terminal courant (panneau d'agents).
⚠️ En mode panes, le corps d'une définition d'agent **remplace** le system prompt par défaut du
teammate (en in-process il s'y ajoute — doc Claude Code, agent teams) : chaque rôle porte donc un
« Cadre de travail » autonome.
Désinstaller : `/plugin uninstall agent-teams@claude-setup --scope project`.

> 🔖 **Mainteneur : à CHAQUE modification de ce plugin, bump `version` dans
> `.claude-plugin/plugin.json`** — sinon les projets ne voient pas la mise à jour via
> `/plugin marketplace update claude-setup`.

> 🧑‍🤝‍🧑 Un projet **solo/n8n** n'a pas besoin de ce plugin — c'est précisément pourquoi il est sorti du cœur.
