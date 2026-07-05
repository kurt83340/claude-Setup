---
name: team
description: Délègue une feature ou une mission à une équipe de teammates visibles en tmux — plan d'équipe validé par l'utilisateur (rôles, topologie de communication), worktree par codeur, task list native, suivi, merge, débrief mémoire, clôture propre. À invoquer quand l'utilisateur veut paralléliser une spec sur plusieurs agents (« lance une équipe », « délègue à des agents »). Requiert les agent teams (câblés dans settings.json du template).
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, SendMessage, TaskCreate, TaskUpdate, TaskList, Skill, Bash(git worktree:*), Bash(git branch:*), Bash(git status), Bash(git log:*), Bash(git diff:*), Bash(git merge:*), Bash(tmux -V), Bash(grep:*)
disable-model-invocation: false
---

# /team — Orchestrer une équipe de teammates sur une feature

Tu es le **LEAD**. Le protocole (rôles, périmètres, cycle de vie lead-owned/user-owned,
topologie hub-and-spoke/mesh, débrief mémoire) = la rule
[`agent-teams.md`](../../rules/agent-teams.md), auto-chargée. Ce skill = la **séquence opératoire**.

**Argument** : `/team <spec-id>` (ex. `/team 001-erp-connector`) ou `/team "<mission libre>"`.

## Étape 0 — Préflight

```bash
grep -q 'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS' .claude/settings.json && echo "✅ teams câblées" || echo "❌ flag absent de settings.json"
tmux -V || echo "⚠️ tmux absent → teammateMode retombera en in-process (agents dans TON terminal, pas en panes)"
git status --short > /dev/null 2>&1 && echo "✅ repo git" || echo "❌ pas un repo git (worktrees impossibles)"
```

- Spec fournie ? Vérifie que `.claude/docs/conception/specs/<id>/tasks.md` existe (sinon propose `/spec` d'abord).
- Un point ne passe pas → le dire à l'utilisateur et demander AVANT de continuer en mode
  dégradé (subagents séquentiels, invisibles).

## Étape 1 — Plan d'équipe (validation utilisateur OBLIGATOIRE)

1. Lis `specs/<id>/tasks.md` → groupes de tâches parallélisables **sans chevauchement de fichiers**.
2. Mappe chaque groupe → un rôle : `front-end`, `back-end`, `tester`, `worker` (généraliste),
   ou **ad-hoc** (prompt sur mesure, même protocole). Ajoute `reviewer` dès 2 codeurs.
3. **2 à 4 teammates codeurs MAX** (au-delà : merge hell).
4. Propose le plan à l'utilisateur :
   - rôles + tâches par teammate + worktrees ;
   - **topologie de communication** — défaut hub-and-spoke ; propose un mesh scopé si deux
     rôles doivent négocier (ex. contrat d'API front ↔ back) ;
   - rappel cycle de vie : les teammates spawnés par `/team` sont **lead-owned** → je les
     fermerai à la clôture (Étape 8).
5. → **Validation utilisateur avant de spawner.**

## Étape 2 — Tasks natives (tableau de bord partagé)

- `TaskCreate` : 1 task par sous-tâche (subject = l'item de tasks.md ; description =
  contexte + DoD + fichiers probables). Dépendances : `TaskUpdate` `addBlockedBy`.
- La task list native = tableau de bord de la session ; `specs/<id>/tasks.md` reste la
  source **versionnée** (tu y recopies l'état final en Étape 8).

## Étape 3 — Worktrees (teammates qui codent)

```bash
git worktree add ../<repo>--<teammate> -b feature/<00X>-<slug>--<teammate>
```

1 worktree par codeur. `reviewer` (lecture seule) : pas de worktree — il lit le repo
principal et les worktrees.

## Étape 4 — Spawn

Pour chaque teammate (rôle préconfiguré = son nom d'agent ; ad-hoc = nom + prompt), la
mission contient :

- le contexte spec (liens vers `spec.md` / `plan.md`) + SA liste de tâches (ids des tasks natives) ;
- SON worktree (chemin absolu) — il ne travaille QUE là ;
- la consigne rapport : **résultat + fichiers touchés + échecs/pièges + reste à faire**, via
  `SendMessage`, AVANT de passer idle ;
- la **topologie** décidée en Étape 1 : « tout passe par moi » OU « échange direct avec <X>
  sur <sujet> uniquement ; le reste passe par moi » ;
- claim tes tasks (owner) et fais-les vivre (`in_progress` → `completed`).

## Étape 5 — Suivi

Les teammates bossent (panes tmux visibles). Toi : réagis aux `SendMessage` + idle
notifications ; `TaskList` pour l'avancement ; trace persistée dans
`.claude/.cache/team-progress.log` (hook TaskCompleted). Débloque, réassigne, envoie le
reviewer sur les diffs au fil de l'eau. Tu restes disponible pour l'utilisateur.

## Étape 6 — Débrief mémoire (à CHAQUE rapport — pas seulement à la fin)

cf. rule § Lead : échecs → HANDOFF « Échecs tentés » ; pièges/gotchas → `/lecon` ou
code-map ; décision structurante → `/adr` ; avancement → tasks natives + ROADMAP `X/Y`.
**Un rapport non persisté = savoir perdu** (le contexte teammate meurt avec la session).

## Étape 7 — Merge + vérif

Un teammate a fini SA branche → review (reviewer ou toi) → merge dans la branche
d'intégration → **tests après CHAQUE merge** (jamais deux merges sans vert entre).

## Étape 8 — Clôture (propre)

1. Recopie l'état final des tasks natives → coche `specs/<id>/tasks.md` (source versionnée).
2. Ferme **UNIQUEMENT les teammates que CE skill a spawnés** (lead-owned). Un teammate
   demandé par l'utilisateur (avant ou pendant) est **user-owned** : il persiste — signale
   juste à l'utilisateur qu'il est encore actif.
3. `git worktree remove ../<repo>--<x>` pour chaque worktree mergé + `git worktree prune`.
4. Tous les tasks ✅ → propose `/feature-done <id>`.
5. `/handoff` (le Journal note : « session équipe : N teammates, X tasks, branches mergées »).

## Anti-patterns

- ❌ Spawner sans plan validé (Étape 1) — l'utilisateur choisit la topologie et voit le découpage
- ❌ > 4 teammates codeurs, ou 2 teammates sur les MÊMES fichiers
- ❌ Fermer un teammate user-owned (seul l'utilisateur décide)
- ❌ Fermer la session sans débrief/merge (`/resume` ne restaure pas l'équipe)
- ❌ Laisser l'état final uniquement dans la task list native (recopier dans `specs/<id>/tasks.md`)
