# Agent teams — protocole d'équipe (SOURCE UNIQUE)

> Protocole multi-agent du template (lead + teammates). Auto-chargée dans **chaque** session
> du repo — y compris les teammates (qui sont des sessions Claude Code complètes).
> Câblage : `settings.json` → `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "tmux"`.
> Orchestration d'une feature : skill [`/team`](../skills/team/SKILL.md). Rôles : [`agents/`](../agents/README.md).

## Identifie ton rôle

- **Lead** = la session à qui l'utilisateur parle ; c'est elle qui spawne l'équipe.
- **Teammate** = session spawnée par le lead — rôle préconfiguré (`worker`, `front-end`,
  `back-end`, `tester`, `reviewer`) **ou ad-hoc** (nom + prompt). Si ta mission vient d'un
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

| Critère           | Teammate (session visible tmux)               | Subagent (Task tool, invisible)             |
| ----------------- | --------------------------------------------- | ------------------------------------------- |
| Durée / autonomie | Longue, multi-tours, doit être observable     | Courte, one-shot                            |
| Écrit du code     | ✅ — dans SON worktree                        | À éviter (pas d'isolation worktree)         |
| Exemples          | Sous-tâche de spec, review continue           | Recherche/lecture, `doc-maintainer`, audits |
| Retour            | `SendMessage` + idle notification + task list | Résultat = retour du Task tool              |

Défaut du template : **le travail de feature part en teammates** (visibles) ; les besognes
courtes (scan, doc) restent en subagents.

**Cycle de vie — qui possède un teammate, qui le ferme :**

- Teammate spawné à **ton initiative** (délégation que TU as décidée, ex. via `/team`) →
  **lead-owned** : tu le fermes toi-même après débrief + merge. Pas de session zombie.
- Teammate **demandé par l'utilisateur** (« lance-moi un agent front-end sur X ») →
  **user-owned** : il **persiste**. Tu ne le fermes JAMAIS de ta propre initiative — seul
  l'utilisateur décide (il veut souvent l'observer ou lui parler dans son pane tmux).
  Doute sur le propriétaire ? Demande.
- ⚠️ Limitation native : aucun teammate ne survit à la fin de TA session (`/resume` ne les
  restaure pas). « Persistant » = pour la durée de la session lead ; la persistance
  inter-sessions passe par le **débrief mémoire** + HANDOFF.

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

**Suivi** : idle notifications (automatiques) + task list native (`TaskCreate`/`TaskList`,
miroir de `specs/00X/tasks.md`) + trace `.claude/.cache/team-progress.log` (hook TaskCompleted).
⚠️ `/resume` ne restaure PAS les teammates → débriefe et merge **avant** de fermer la session.
Les **prompts de permission** des teammates remontent chez TOI (un teammate ne peut pas
s'auto-approuver) — c'est toi qui approuves, dans ta session.

**Débrief mémoire (OBLIGATOIRE, à chaque rapport reçu)** — l'unique canal entre le contexte
d'un teammate et la mémoire projet :

1. Échecs tentés / impasses → HANDOFF § « Échecs tentés » (via `/handoff` en fin de session)
2. Pièges / gotchas non-déductibles → `/lecon` (ou `code-map.md` § Gotchas si couplage)
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
