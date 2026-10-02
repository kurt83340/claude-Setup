# Plugin `agent-teams`

> **Exécution d'équipe** du template claude-Setup, packagée en plugin Claude Code installable par projet.
> Marketplace `claude-setup` (racine du repo : [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)).

| Composant | Quoi |
| --- | --- |
| Skill [`team`](skills/team/SKILL.md) → **`/agent-teams:team <spec-id>`** | Orchestre une équipe de teammates tmux : plan validé, 1 worktree/codeur, task list native, TDD opt-in, suivi, merge, débrief mémoire, clôture |
| Agents [`worker`](agents/worker.md) · [`front-end`](agents/front-end.md) · [`back-end`](agents/back-end.md) · [`tester`](agents/tester.md) | **Rôles d'exécution** teammate (généraliste, UI, serveur, QA) — auto-découverts à l'installation |
| Hook [`team-invariants.py`](hooks/team-invariants.py) (PreToolUse `Agent` + SessionStart compact/clear) | Invariants d'équipe **au spawn** : § Teammate ajouté au prompt de chaque teammate, § Lead au lead (1×/session, ré-armé après compaction) |
| Script [`teams.py`](skills/team/scripts/teams.py) → **`/agent-teams:team on · off · status`** | Interrupteur : flag + `teammateMode` dans les settings (local > projet > user), retrait d'une rule héritée |
| Hook [`teamtask-log.py`](hooks/teamtask-log.py) (TaskCreated/TaskCompleted/TeammateIdle) | Trace JSON de progression d'équipe → `.claude/.cache/team-progress.log` |

## Opt-in : rien dans le cœur, rien d'auto-chargé (v1.5.0 du template, plugin 1.2.0)

Le cœur du template ne câble pas les agent teams : le flag `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
monte une équipe à chaque session et transforme tout subagent nommé en teammate (doc agent teams).

- **Interrupteur** = `/agent-teams:team on | off | status` ([`teams.py`](skills/team/scripts/teams.py),
  `--dry-run` montré avant tout changement) : `on` pose `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`
  (+ `teammateMode: "auto"` si rien ne le définit) puis demande une relance ; `off` retire le flag, ou le
  met à `"0"` s'il reste à 1 ailleurs (settings user, export shell) — effet immédiat sur les prochains spawns.
  `--scope project` (défaut) · `local` · `user`. `/agent-teams:team <spec>` avec l'équipe coupée propose `on`.
- **Invariants au spawn** (plugin 1.2) : [`invariants.md`](skills/team/invariants.md) n'est jamais copié
  dans `.claude/rules/`. Le hook `team-invariants.py` ajoute § Teammate à la fin du prompt de chaque
  teammate (rôle ou ad-hoc) et injecte § Lead au lead au 1er spawn — 0 token pour les sessions sans
  équipe (avant : rule auto-chargée, ~1,9k tokens à CHAQUE session du projet). Une rule héritée
  `.claude/rules/agent-teams.md` est déplacée dans `.claude/.cache/` par `on` / `off`.
- **Plugin absent, flag à 1** : le hook SessionStart du cœur le signale au démarrage (jamais d'équipe sans
  protocole en silence) — `CLAUDE_TEAMS_PLUGIN_CHECK=off` pour le taire.
- Protocole complet : [`skills/team/protocole.md`](skills/team/protocole.md) (lu par `/agent-teams:team`).
- Restent dans le **cœur** (dépendances des skills cœur) : `reviewer` et les explorateurs
  `explore-code` / `explore-docs` / `explore-memoire` (`.claude/agents/`), utilisables en subagents sans équipe.

## Installer (dans un projet)

```bash
/plugin marketplace add kurt83340/claude-Setup          # une fois
claude plugin install agent-teams@claude-setup --scope project
# puis, dans Claude Code : /agent-teams:team on   → relance → /agent-teams:team <spec-id>
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
