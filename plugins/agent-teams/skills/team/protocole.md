# Agent teams — protocole complet (source unique)

> Version longue du protocole d'équipe (politique teammate vs subagent, cycle de vie, topologie,
> worktrees, spawn, suivi, débrief, mémoire, hooks). Lue par `/agent-teams:team` (Étape 0) ; jamais
> auto-chargée. Les **invariants** courts (§ Teammate 6 règles, § Lead 5 invariants) vivent dans
> `invariants.md` et sont **injectés au spawn** par le hook du plugin (v1.2.0 — avant : rule copiée
> dans `.claude/rules/`, ~1,9k tokens à chaque session du projet, équipe ou pas) : § Teammate à la
> fin du prompt de chaque teammate, § Lead au lead au 1er spawn de la session.

> Interrupteur : `/agent-teams:team on | off | status` (`scripts/teams.py`) — `on` pose
> `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "auto"` dans les settings du projet
> (ou `settings.local.json`), `off` le retire (ou `"0"` s'il reste à 1 en user / shell).
> Orchestration d'une feature : **`/agent-teams:team`** — plugin `agent-teams` (rôles d'exécution
> `worker`/`front-end`/`back-end`/`tester` + hook de trace ; `/plugin install agent-teams@claude-setup`).
> Rôles lecture seule du cœur (`reviewer`, `explore-*`) : [`agents/`](../agents/README.md).
> ⚠️ **Câblage des défs** : toute déf d'agent teammate (`agents/*.md`) DOIT lister **`SendMessage`** dans son `tools:`. Sinon, spawné **nommé** (donc teammate), l'agent n'a aucun canal pour livrer son rapport — son texte final ne remonte PAS au lead → rapport perdu, idle muet, zombie qui ping. (Corrigé v0.8.1.)

## Identifie ton rôle

- **Lead** = la session à qui l'utilisateur parle ; c'est elle qui spawne l'équipe.
- **Teammate** = session spawnée par le lead — rôle préconfiguré (`worker`, `front-end`,
  `back-end`, `tester`, `reviewer`, `explore-*`) **ou ad-hoc** (nom + prompt). Si ta mission vient d'un
  lead (pas de l'utilisateur), tu es teammate : applique § Teammate, même sans rôle préconfiguré.

## § Teammate (préconfiguré OU ad-hoc — pas d'exception)

**Communication**

- Livre TOUJOURS ton résultat au lead via `SendMessage` **AVANT de passer idle**. Ne compte
  jamais sur ton texte de réponse : il n'arrive pas au lead (seul un idle ping passe).
- Format du rapport : **résultat + fichiers touchés + échecs tentés / pièges découverts +
  reste à faire / blocages**. Les échecs et pièges sont OBLIGATOIRES : c'est la matière
  première de la mémoire projet — toi tu ne peux pas la persister, le lead si.
- Bloqué ? `SendMessage` immédiat au lead (le blocage + ce dont tu as besoin).
- L'utilisateur peut te parler **directement dans ton pane** (documenté). Si tu attends une
  décision de LUI : pose ta question en **texte** dans ton pane (le widget interactif n'est
  pas garanti chez un teammate) **ET** préviens le lead par `SendMessage` (« en attente
  décision utilisateur sur X ») — sinon il ne voit qu'un idle inexpliqué. Rapporte-lui
  ensuite la décision reçue.
- Autres teammates : ne leur écris directement QUE si ta mission l'autorise explicitement
  (topologie « mesh », accordée par le lead). Par défaut : **tout passe par le lead**.
- Si le lead utilise la task list partagée : claim ta tâche (owner), passe-la `in_progress`
  puis `completed` — c'est le tableau de bord du lead.

**Périmètre (anti-collision)**

- Écris uniquement dans les fichiers de TA tâche : `src/...`, `tests/...`, `specs/<ta-spec>/...`.
- Docs partagés **INTERDITS en écriture** : `HANDOFF.md`, `ROADMAP.md`, `CHANGELOG.md`,
  `code-map.md`, `adr/README.md`, `lecons.md`. Tu rapportes, le lead consolide.
- Numérotation specs `00X` / ADR `00XX` : allouée par le **lead** uniquement (sinon course).
- Ne committe **JAMAIS** `.claude/docs/HANDOFF.md` — même dans ton worktree (conflit garanti
  quand le lead merge). Ton état local vit dans ton rapport SendMessage, pas dans un fichier versionné.
- Tu ne peux pas spawner de teammates (limitation native) — demande au lead.

**Fin de tâche** : vérifie ta zone (tests/lint ciblés) → `SendMessage` rapport complet →
reste disponible (pas de shutdown sauf demande du lead).

## § Lead

**Propriété** : toi seul écris les docs partagés et alloues les numéros specs/ADR.

**Politique de délégation — teammate vs subagent :**

| Critère           | Teammate (nommé — pane ou panneau, visible)   | Subagent (sans `name`, invisible)      |
| ----------------- | --------------------------------------------- | -------------------------------------- |
| Durée / autonomie | Toute durée, observable (besognes courtes ok) | Courte, one-shot                       |
| Écrit du code     | ✅ — dans SON worktree                        | À éviter (pas d'isolation worktree)    |
| Exemples          | Tout agent quand l'équipe est active          | Équipe coupée : recherche, audits, doc |
| Retour            | `SendMessage` + idle notification + task list | Résultat = retour du Task tool         |

Défaut du template, **équipe active** : **tout agent est nommé** (`name` au spawn), besognes
courtes comprises (scan, relevé, doc, `doc-maintainer`) → il devient teammate et s'ouvre dans son
pane : l'utilisateur voit tout ce qui tourne. Délègue au maximum (lectures larges, relevés,
exécutions bornées, résumé court en retour) pour que ta session orchestre et dure ; ferme chaque
agent dès son rapport débriefé (§ Cycle de vie). Un agent sans nom tourne en arrière-plan,
invisible : réservé aux sessions sans équipe.

**Cycle de vie — qui ferme un teammate, et quand :**

- Travail fini (rapport reçu et **débriefé**, branche **mergée** s'il code) → **tu le fermes** :
  `SendMessage` avec `{"type": "shutdown_request"}`. Même règle qu'il ait été spawné à ton
  initiative (ex. via `/agent-teams:team`) ou à la demande de l'utilisateur (« lance-moi un agent
  front-end sur X ») : un teammate fini ne reste pas ouvert. Pas de session zombie.
- Seule exception : une **étape suivante annoncée** dépend de lui (correction après review, suite
  prévue de sa tâche) → garde-le, dis-le à l'utilisateur, et ferme-le dès que cette étape est faite.
- Teammate encore au travail → tu ne le fermes pas ; à la clôture, signale-le à l'utilisateur.
- Pane mort : il reste listé (`ListAgents`). Repère-le
  (`tmux list-panes -a -F '#{pane_id} #{pane_dead}'` → `1`) et ferme-le : `tmux kill-pane -t %N`.
- ⚠️ Limitation native : aucun teammate ne survit à la fin de TA session (`/resume` ne les
  restaure pas) → débriefe et merge **avant** de fermer ; ce qui doit durer d'une session à
  l'autre passe par le **débrief mémoire** + HANDOFF.

**Topologie de communication (à fixer au spawn, jamais implicite) :**

- Défaut : **hub-and-spoke** — chaque teammate ne parle qu'au lead. Prévisible, pas de cacophonie.
- **Mesh (opt-in)** : si l'utilisateur le demande, ou si la tâche l'exige (ex. front ↔ back
  qui négocient un contrat d'API), autorise-le EXPLICITEMENT dans le prompt de mission, scopé :
  « tu peux échanger directement avec <X> sur <sujet> ; tout le reste passe par moi ».
- Nativement, les teammates PEUVENT s'écrire entre eux — c'est le prompt de mission qui fixe
  la règle. Dans tous les cas, le **débrief mémoire** reste au lead.
- L'utilisateur demande un agent sans préciser la topologie ? Confirme-la en une question.

**Worktrees** (dès 2 teammates qui codent) — 1 teammate-codeur = 1 worktree :

```bash
git worktree add ../<repo>--<teammate> -b feature/<00X>-<slug>--<teammate>
# après merge : git worktree remove ../<repo>--<teammate> && git worktree prune
```

Les hooks utilisent `${CLAUDE_PROJECT_DIR}` → worktree-safe. Le reviewer (lecture seule)
n'a pas besoin de worktree.

**Spawn — TOUJOURS depuis la racine du repo :**

- Un `cd` fait en Bash **persiste** entre les appels et est **hérité** par tout teammate
  spawné ensuite : il démarre sa session Claude Code dans ce sous-dossier. Le `CLAUDE.md`
  racine est bien trouvé (remontée d'arborescence), mais ses `@-imports` pointent alors
  **hors du cwd** → dialogue bloquant « Allow external CLAUDE.md file imports? » au
  démarrage. Et l'approbation étant mémorisée **par chemin** dans `~/.claude.json`, celle
  donnée pour la racine ne couvre PAS le sous-dossier. Réflexe avant tout spawn :
  `cd "$(git rev-parse --show-toplevel)"`.
- ⚠️ Ce blocage est **invisible** depuis le lead : un teammate figé sur un dialogue
  interactif de démarrage n'émet AUCUN signal — pas d'erreur, pas d'idle ping, tes
  `SendMessage` s'empilent non lus. Indistinguable d'un agent mort → applique § Suivi
  (capture-pane) avant de conclure.

**Suivi** : idle notifications (automatiques) + task list native (`TaskCreate`/`TaskList`,
miroir de `specs/00X/tasks.md`) + trace `.claude/.cache/team-progress.log` (hook TaskCompleted).
⚠️ `/resume` ne restaure PAS les teammates → débriefe et merge **avant** de fermer la session.
Les **prompts de permission** des teammates remontent chez TOI (un teammate ne peut pas
s'auto-approuver) — c'est toi qui approuves, dans ta session.
⚠️ **Teammate silencieux ≠ teammate mort.** Avant de respawner (mode panes ; en in-process : ouvrir le
teammate dans le panneau d'agents) : `tmux capture-pane -p -t <pane>`
— un dialogue interactif de démarrage (imports CLAUDE.md, trust) fige tout sans émettre aucun
signal, et un respawn re-bloquera pareil (+ travail perdu). Déblocage : `tmux -L <socket>
send-keys -t <pane> Enter` (« Yes » est présélectionné ; socket trouvable via `ls /tmp/tmux-$UID/`).

**Débrief mémoire (OBLIGATOIRE, à chaque rapport reçu)** — l'unique canal entre le contexte
d'un teammate et la mémoire projet :

1. Échecs tentés / impasses → HANDOFF § « Échecs tentés » (via `/handoff` en fin de session)
2. Pièges / gotchas non-déductibles → `/lecon` (ou `code-map-gotchas.md` si le piège vise un
   fichier/une zone — jamais dans `code-map.md`, auto-chargé)
3. Décision structurante prise en délégation → `/adr`
4. Avancement → cocher `specs/00X/tasks.md` + ROADMAP `X/Y`

Un rapport non persisté = savoir **perdu** (le contexte teammate meurt avec la session).

## Mémoire en équipe (ce qui survit, ce qui meurt)

- **Auto-memory** : keyée par repo git → **partagée** entre worktrees et teammates (écritures
  concurrentes possibles) ; machine-locale, non versionnée. → Traite-la comme un **cache**,
  jamais comme la source de vérité.
- **Source de vérité durable** = les docs versionnées (HANDOFF, lecons, ADR, CHANGELOG,
  code-map). Consolidation : `/doc-health` (étape auto-memory) propose la promotion des
  patterns stables en rule / leçon / ADR.
- **Contexte teammate** : meurt à la fin de session → le débrief (§ Lead) est le seul canal.

## Hooks en multi-agent

- Snapshot pré-compaction : **par session** (`.cache/handoff-snapshot-<session_id>.md`) — zéro collision.
- Snapshot fin de session : `.cache/session-end-snapshot.md` — filet si `/handoff` oublié,
  réinjecté au prochain démarrage s'il est plus frais que `HANDOFF.md`, puis consommé.
- Rappel `/handoff` (Stop) : lead-only ; pour une session teammate lancée hors team-mode,
  exporter `CLAUDE_HANDOFF_REMINDER=off`.
