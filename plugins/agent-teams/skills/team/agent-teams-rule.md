# Agent teams — invariants d'équipe (auto-chargés)

> Installée dans `.claude/rules/agent-teams.md` par l'**activation** du plugin `agent-teams`
> (1er `/agent-teams:team`) — jamais présente dans un projet qui n'utilise pas d'équipe (v1.5.0 :
> sortie du cœur, elle pesait ~1,8k tokens sur CHAQUE session). Rule volontairement **courte** :
> chargée dans chaque session du projet, teammates compris. Le **protocole complet** (politique
> teammate vs subagent, cycle de vie, topologie, worktrees, spawn, suivi, débrief, hooks) =
> `skills/team/protocole.md` du plugin, lu par `/agent-teams:team`. Câblage posé par l'activation :
> `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "auto"`. Rôles lecture seule du
> cœur (`reviewer`, `explore-*`) : `.claude/agents/`.

## Identifie ton rôle

- **Lead** = la session à qui l'utilisateur parle ; elle spawne l'équipe.
- **Teammate** = session spawnée par un lead — rôle préconfiguré (`worker`, `front-end`, `back-end`,
  `tester`, `reviewer`, `explore-*`) **ou ad-hoc**. Mission reçue d'un lead → tu es teammate : § Teammate.

## § Teammate — 6 règles, pas d'exception

1. Livre ton résultat au lead via **`SendMessage` AVANT de passer idle** : résultat + fichiers touchés +
   **échecs tentés / pièges** (obligatoires : matière première de la mémoire projet) + reste à faire.
   Ton texte de réponse n'arrive **pas** au lead.
2. Bloqué, ou décision utilisateur attendue → `SendMessage` immédiat au lead (+ question en texte dans ton pane).
3. Périmètre : **uniquement** les fichiers de TA tâche (`src/`, `tests/`, `specs/<ta-spec>/`). Docs partagés
   **interdits en écriture** : HANDOFF, ROADMAP, CHANGELOG, code-map (+ gotchas), adr/README, lecons — tu rapportes, le lead consolide.
4. Ne committe **JAMAIS** `.claude/docs/HANDOFF.md`, même dans ton worktree (conflit garanti au merge).
5. Numéros specs `00X` / ADR `00XX` : alloués par le **lead**. Autres teammates : tout passe par le lead,
   sauf mesh explicitement accordé dans ta mission. Tu ne peux pas spawner (limitation native) — demande au lead.
6. Fin de tâche : tests/lint ciblés → rapport `SendMessage` complet → reste disponible (pas de shutdown sans le lead).

## § Lead — 5 invariants

1. Toi seul écris les docs partagés et alloues les numéros. Chaque rapport reçu est **débriefé en mémoire**
   (échecs → HANDOFF § Échecs via `/handoff` ; pièges → `/lecon` ou `code-map-gotchas.md` ; décision → `/adr` ;
   avancement → `specs/00X/tasks.md` + ROADMAP) — sinon le savoir meurt avec le teammate.
2. Spawn **toujours depuis la racine** : `cd "$(git rev-parse --show-toplevel)"` — un `cd` hérité fige le
   teammate sur le dialogue d'imports CLAUDE.md, **sans aucun signal** (indistinguable d'un agent mort).
3. 1 teammate-codeur = 1 worktree : `git worktree add ../<repo>--<x> -b feature/<00X>-<slug>--<x>`
   (après merge : `git worktree remove … && git worktree prune`). Hooks `${CLAUDE_PROJECT_DIR}` = worktree-safe.
4. Teammate spawné à **ton** initiative = lead-owned (tu le fermes après débrief + merge) ; demandé par
   **l'utilisateur** = user-owned (tu ne le fermes jamais de toi-même). Doute ? Demande.
5. `/resume` ne restaure pas les teammates → débriefe et merge **avant** de fermer. Teammate silencieux ≠ mort :
   `tmux capture-pane -p -t <pane>` avant tout respawn. Leurs prompts de permission remontent chez toi.

> Défs d'agents teammate : **`SendMessage` OBLIGATOIRE dans `tools:`** (sinon rapport perdu, idle muet).
> Hooks : snapshots **par session** ; rappel `/handoff` (Stop) lead-only — teammate hors team-mode :
> `CLAUDE_HANDOFF_REMINDER=off`. Auto-memory partagée entre worktrees = **cache**, jamais source de vérité.
