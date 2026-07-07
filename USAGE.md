# USAGE — Comment utiliser ce template

> Guide pratique : skills + agent + hooks + workflows au quotidien.

---

## 🚀 Setup d'un nouveau projet (à lire EN PREMIER)

### Procédure complète (6 étapes, ~5 min)

```bash
# 1. Copier le template (exclut l'exemple ACME, test, la CI, et la source plugins/marketplace)
rsync -av --exclude='EXAMPLES/' --exclude='test/' --exclude='.github/' --exclude='.git/' \
  --exclude='plugins/' --exclude='.claude-plugin/' \
  /chemin/vers/template/ /chemin/vers/mon-nouveau-projet/

# 2. Aller dedans
cd /chemin/vers/mon-nouveau-projet/

# 3. ⚠️ CRITIQUE — Hooks exécutables (sinon ils bloquent au 1er run)
chmod +x .claude/hooks/*.py .claude/hooks/*.sh

# 4. Git init pour rollback possible
git init && git add . && git commit -m "chore: snapshot pre-init"

# 5. Lancer Claude Code
claude
```

> 🔌 **Prérequis recommandé : MCP `context7` connecté en user-level** (installé une fois,
> dispo dans toutes les sessions). La rule [`doc-lookup`](.claude/rules/doc-lookup.md) du
> template s'appuie dessus (doc officielle versionnée) pour `/conception`, `/debug`, les
> explorateurs et les teammates ; fallback automatique WebFetch/WebSearch s'il est absent.

Dans la session Claude :

```
/init-from-template
```

Claude va :

1. **Vérifier les prérequis** (chmod hooks, git initialisé, python3 dispo)
2. **Poser 10 questions** via AskUserQuestion (3 batches) :
   - Batch 1 : `PROJECT_NAME`, `PROJECT_FOLDER`, **type de projet**
   - Batch 2 : `CLIENT_NAME`, `NOM_DECIDEUR`, `EMAIL_DECIDEUR`, `TON_NOM`, `TON_EMAIL`
   - Batch 3 : `COMMANDE_INSTALL`, `COMMANDE_TESTS`, `COMMANDE_RUN`
3. **Substituer les CORE placeholders** auto (10 substitutions sur ~370 placeholders — le reste est CONTENT à remplir au fil de l'eau)
4. **Lancer `cleanup-for-type.py`** selon le type : adapte le template **et retire les artefacts de maintenance DU template** (`.github/` self-CI, `test/`, `EXAMPLES/`, skills bootstrap `init-from-template`/`adopt-template`) → le projet généré démarre **propre, sans CI héritée**
5. **Proposer d'installer le plugin stack** si pertinent (type `automation-n8n` → plugin **officiel** `n8n-mcp-skills` via `/plugin marketplace add czlonkowski/n8n-skills` ; `bdd-migration` → `db-migration@claude-setup`)
6. **Te proposer le commit initial** : `feat: init projet <nom> depuis template`

### Les 5 types de projet (impact sur cleanup)

| Type             | Impact   | Skills installés                              | Use case                         |
| ---------------- | -------- | --------------------------------------------- | -------------------------------- |
| `script-jetable` | **-80%** | 2 (handoff, lecon)                      | 1-shot Python, < 1 jour          |
| `python-app`     | léger    | 12 (cœur)                                     | App Python (FastAPI, scripts...) |
| `web-app`        | léger    | 12 (cœur)                                     | Next.js, React, etc.             |
| `automation-n8n` | léger    | 12 cœur + plugin officiel `n8n-mcp-skills` (×14) | Workflow n8n + helpers Python |
| `bdd-migration`  | léger    | 12 cœur + plugin `db-migration`               | Migration BDD avec Alembic       |

### Vérification post-init

> ℹ️ L'init a déjà vérifié les CORE (`render.py --check`) **avant** le cleanup — le script est
> ensuite retiré avec le scaffolding du template. Re-check possible sans script :

```bash
# 1. Aucun placeholder CORE restant ? (rien trouvé = ✅). Périmètre SUBSTITUÉ uniquement :
#    les templates bundlés de /spec ({{SPEC_*}}) et STRUCTURE/USAGE gardent leurs {{...}} d'exemple — normal.
grep -rEn '\{\{[A-Z]{2,}_[A-Z][A-Z0-9_]+\}\}' CLAUDE.md README.md .env.example .claude/CLAUDE.md .claude/docs/ .claude/rules/ 2>/dev/null && echo "❌ CORE restants" || echo "✅ aucun CORE restant"

# 2. Premier commit du projet rempli
git add -A
git commit -m "feat: init projet <nom> depuis template"
```

### Prochaines étapes après init

1. **Remplir `cadrage/README.md`** (verbatim demande client + interlocuteurs)
2. **Planifier le kickoff** → archiver compte-rendu dans `cadrage/reunions/`
3. **Quand brief mûr** → remplir `conception/PRD.md`
4. **Quand archi décidée** → `conception/ARCHITECTURE.md`
5. **Démarrer 1ère feature** : `/spec "<titre>"`

### Projet EXISTANT (brownfield) → `/adopt-template`

Ton projet a déjà du code et une histoire ? **Ne pas** utiliser `/init-from-template`. À la place :

```bash
cd /chemin/vers/projet-existant     # working tree PROPRE (commit/stash avant)
rsync -av --ignore-existing \
  --exclude='EXAMPLES/' --exclude='test/' --exclude='.github/' \
  --exclude='plugins/' --exclude='.claude-plugin/' \
  --exclude='.git/' --exclude='README.md' --exclude='.env.example' \
  /chemin/vers/template/ .
chmod +x .claude/hooks/*.py .claude/hooks/*.sh
# (Recommandé) Dépose MAINTENANT tes matériaux — le skill les ingère :
#   docs client → .claude/docs/cadrage/documents/   tickets → cadrage/tickets/
#   transcriptions → cadrage/reunions/
claude   # puis : /adopt-template
```

`--ignore-existing` = **l'existant gagne toujours** (tes CLAUDE.md / settings.json /
.gitignore ne sont pas touchés). Le skill propose ensuite : merges des collisions **en diff**
(jamais d'overwrite), questions CORE **pré-remplies** depuis tes manifests, et
**rétro-remplissage** de la doc depuis le projet (stack.md ← manifests, code-map ←
`/codemap`, cadrage ← README existant, HANDOFF ← git log, ADRs rétroactifs optionnels).

### Troubleshooting init

- **`chmod: No such file or directory`** → tu es au mauvais endroit, vérifie `cd`
- **`render.py: 0 fichiers à scanner`** → le rsync n'a rien copié (vérifie source)
- **`/init-from-template` pas trouvé** → relance `claude` (skills scannés au démarrage)
- **CORE manquants après render** → ajoute-les au vars.json et relance

---

## 🧠 Comprendre AVANT d'utiliser : les 3 layers de mémoire

Claude Code a 3 couches de mémoire complémentaires — **Stable** (`CLAUDE.md` + `.claude/rules/*`), **Patterns** (auto-memory, machine-local) et **État** (`HANDOFF.md`). Ne les confonds pas.

→ **Détail canonique** (qui écrit quoi / survit à quoi / versionné) : [.claude/rules/template-maintenance.md § Les 3 layers de mémoire](.claude/rules/template-maintenance.md). Source unique — évite le drift.

**`/resume` vs HANDOFF.md** : `/resume` (built-in) garde 100 % du contexte de la session précédente (reprise même journée) ; `HANDOFF.md` sert quand tu changes de machine, clones ailleurs, partages, ou démarres à froid après plusieurs jours. **Complémentaires.**

## 📅 Workflow quotidien

### Démarrer une session

1. Lance Claude Code : `claude` (ou `claude --resume` si reprise même journée)
2. Claude charge automatiquement :
   - `CLAUDE.md` (racine — index projet) **+** `.claude/CLAUDE.md` (template/skills) — les deux via @-imports
   - `.claude/docs/HANDOFF.md` (où tu en étais)
   - `.claude/docs/ROADMAP.md` (vue d'avion)
   - Toutes les autres docs référencées
3. **Workflow manuel recommandé** (5 étapes) :
   ```
   1. Lire HANDOFF.md      → reprendre où on en est
   2. Lire ROADMAP.md       → vue d'avion du projet
   3. Lire la spec en cours (lien dans HANDOFF)
   4. git status + git log -5 → ce qui s'est passé
   5. Ask user : "on continue sur X ? ou autre chose ?"
   ```

### Pendant que tu codes

**Automatique (hooks)** :

- 📖 **PreToolUse** : avant chaque édition de fichier dans `src/`, `tests/`, `lib/`, `app/` → Claude reçoit automatiquement les **règles de couplage + intention + gotchas** de code-map.md (le non-déductible) — **tu ne fais RIEN**
- 🔍 **PostToolUse** : si tu écris du code mentionnant `API_KEY`, `deploy`, `RGPD`, `OAuth`, etc. → flag automatique dans `.claude/.growth-suggestions.md`
- 💾 **Auto-memory** : Claude apprend tes patterns (machine-local, dans `~/.claude/projects/.../memory/`)

**Manuel (si besoin)** :

- `/lecon <scope> "<titre>"` → capture rapide d'une observation/bug
- `/adr <scope> "<titre>"` → capture une décision tech structurante
- `/codemap` → après gros refacto, régénère la code-map

### Fin de session

⚠️ **CRITIQUE** : toujours faire ça avant de fermer Claude.

```
/handoff
```

Claude va :

1. Lire git status + log + diff + tests
2. Lire HANDOFF.md actuel
3. Te proposer un nouveau HANDOFF (status / échecs / blockers / next steps)
4. Te demander confirmation avant d'écrire

**Si tu oublies** : hook `Stop` te le rappelle si HANDOFF > 24h avec changements git pending.

### Si Claude compacte le contexte (auto ~90% ou via `/compact`)

Tu ne fais RIEN. Les hooks gèrent :

1. `PreCompact` → snapshot (timestamp + git state) écrit dans `.claude/.cache/` (non-versionné) + marker dans `/tmp/`
2. Claude compacte
3. `SessionStart(matcher: compact)` → re-inject le snapshot
4. Tu continues comme si rien ne s'était passé

## ✅ Livraison d'une feature

Quand tous les tasks de `specs/00X-feature/tasks.md` sont cochés :

```
/feature-done 001-erp-connector
```

Claude va (8 étapes) :

1. Vérifier que tous les tasks sont `[x]` + DoD rempli (sinon demande confirmation)
2. Scanner `plan.md` pour détecter les **décisions tech à promouvoir en ADR** (mots-clés : choisi, retenu, vs, plutôt que)
   - Règle : cross-feature OU survit à la feature → ADR global ; sinon laisser dans `plan.md`
3. **Si ADR créé** : créer fichier + update `docs/adr/README.md` (index par scope) + gérer supersede
4. **Marquer les leçons promues** : `🆕 new` → `📜 → ADR-00XX`
5. **Update ROADMAP.md** : `[~]` → `[x] livré YYYY-MM-DD`
6. **Append CHANGELOG.md** : entry Keep a Changelog (Added/Decided/Fixed)
7. **Update HANDOFF.md** : status feature livrée + next
8. **Update code-map.md** : suggère sections à ajouter si nouveaux modules
9. **Archiver l'idée source** (si la feature vient d'une `idees/YYYY-MM-DD.md`) : status `💡 Backlog` → `✅ Promu en spec 00X`
10. **Suggère commit + tag git** : `v$(date +%Y.%m.%d-%H%M)`

## 🩺 Audit hebdomadaire (~5 min)

```
/doc-health
```

Audit complet qui scanne sans modifier :

| Check                                                   | Seuil                          | Priorité |
| ------------------------------------------------------- | ------------------------------ | -------- |
| Fraîcheur HANDOFF                                       | > 7j                           | 🔴       |
| Growth triggers (API_KEY → ACCESS.md, deploy → RUNBOOK) | > 5 hits                       | 🟢       |
| ADRs manquants (décisions dans plan.md sans ADR)        | ratio > 5                      | 🟢       |
| Leçons `🆕 new` en attente                              | > 5 ou >14j                    | 🟠       |
| Drift code-map vs code                                  | dernier commit > date code-map | 🟠       |
| Placeholders **CORE** non remplis (`{{UPPER_SNAKE}}`)   | > 0                            | 🔴       |
| Placeholders **CONTENT** non remplis (`{{libre}}`)      | informationnel — pas un signal | 🟢       |
| ADRs sans status valide                                 | > 0                            | 🔴       |
| Specs `[~]` EN COURS stalled                            | > 30j                          | 🟠       |
| Idées sans décision                                     | > 30j                          | 🟢       |
| Liens cassés dans docs                                  | > 0                            | 🔴       |
| Patterns auto-memory stables non consolidés             | informationnel                 | 🟢       |

Rapport généré → tu suis les actions par priorité.

## 📋 Cheat sheet — Quand utiliser quoi

| Situation                                  | Skill / Action                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------- |
| Nouveau projet                             | `/init-from-template`                                                         |
| Adopter le template sur un projet EXISTANT | `/adopt-template` (brownfield — merges non-destructifs + rétro-remplissage)   |
| Démarrer une feature                       | `/spec "<titre>"` (scaffold 4 fichiers + ROADMAP)                             |
| Dérouler le pipeline complet (avec gates)  | `/feature "<titre>" [standard·tdd·custom]` — enchaîne spec→conception→code→tests→review→done                             |
| Arrêter le plan d'une feature              | `/conception <spec-id>` (explore → options → décision → plan + revue adverse) |
| Fin de session                             | `/handoff`                                                                    |
| Feature livrée                             | `/feature-done <spec-id>`                                                     |
| Décision tech structurante (cross-feature) | `/adr <scope> "<titre>"`                                                      |
| Décision tech locale à 1 feature           | Section `## Décisions` dans `specs/00X/plan.md`                               |
| Bug/observation à noter rapidement         | `/lecon <scope> "<titre>"`                                                    |
| Débugger un bug non trivial                | `/debug "<symptôme>"` (repro → cause → fix minimal → leçon)                   |
| Idée perso à capturer                      | `/idee "<titre>"`                                                             |
| Refacto majeur sur le code                 | `/codemap`                                                                    |
| Audit hebdo                                | `/doc-health`                                                                 |
| BDD migration (Alembic)                    | plugin `db-migration` (`/plugin install db-migration@claude-setup`)          |
| Workflow batch (HANDOFF + ROADMAP + ADRs)  | Task `doc-maintainer` (agent)                                                 |
| Déléguer une feature à une équipe (tmux)   | `/agent-teams:team <spec-id>` (plugin) — teammates + worktrees + débrief mémoire                   |
| Pivot client                               | `/pivot "<raison>"` (workflow 9 étapes orchestrées)                           |
| Promotion leçon → ADR / rule               | `/lecon promote <date>`                                                       |
| Promotion idée → spec                      | `/idee promote <date>`                                                        |
| Supersede un ADR                           | `/adr supersede <NN> <scope> "<titre>"`                                       |
| Lister tous les ADRs                       | `/adr list [scope]`                                                           |
| Archiver leçons/idées vieilles             | `/lecon archive` ou `/idee archive`                                           |
| Reprendre exactement où on en était        | `/resume` (built-in Claude)                                                   |
| Compaction context (auto)                  | RIEN — hooks gèrent                                                           |
| Édition fichier code (auto)                | RIEN — hook injecte code-map context                                          |
| Mention API_KEY/deploy dans code (auto)    | RIEN — hook flag dans growth-suggestions                                      |

## 🔁 Workflow type pour une feature complète

```
1. Lire ROADMAP.md → choisir la prochaine feature
       ↓
2. /spec "Export PDF"
   → scaffold auto : conception/specs/004-export-pdf/{research,spec,plan,tasks}.md
   → update ROADMAP.md auto
       ↓
3. /conception 004-export-pdf
   → explore (subagents : code + docs + mémoire projet) → 2-3 options → tu tranches
   → plan.md (points de vérification) + tasks.md (partitionné) + revue adverse
       ↓
4. CODE → hooks auto pour contexte code-map + growth detection
       ↓
5. Cocher les tasks au fur et à mesure dans tasks.md
       ↓
6. Si décision tech structurante surgit → /adr <scope> "<titre>"
       ↓
7. Si bug/observation → /lecon <scope> "<titre>"
       ↓
8. /handoff entre les sessions (ou hook auto si oubli)
       ↓
9. Tests verts + DoD rempli → /feature-done 004-export-pdf
       ↓
10. (Optionnel) /doc-health pour audit complet
```

## 🌳 Workflow cadrage (début projet)

**Important** : `.claude/docs/cadrage/` = ce que le CLIENT te file (input EXTERNE). Ne confonds pas avec `.claude/docs/idees/` (tes idées perso, input INTERNE).

```
Demande client reçue
       ↓
1. Update cadrage/README.md (verbatim demande, interlocuteurs, contraintes)
       ↓
2. Si ticket reçu → cadrage/tickets/TICKET-XXX-titre.md
   Si docs reçus → cadrage/documents/YYYY-MM-DD-doc.pdf
   Si réunion → cadrage/reunions/YYYY-MM-DD-kickoff.md
       ↓
3. Une fois cadrage mûr (interlocuteurs OK, contraintes claires) :
   → conception/research.md (brainstorm options)
       ↓
4. Quand approche claire :
   → conception/PRD.md (vision + scope + métriques)
       ↓
5. Validation PRD par décideur :
   → conception/ARCHITECTURE.md (plan technique)
       ↓
6. Architecture validée :
   → conception/tasks.md (plan MVP figé : sous-phases + DoD)
       ↓
7. ROADMAP.md créée à partir de tasks.md
       ↓
8. Specs par feature dans conception/specs/00X-feature/
```

## 🔄 Workflow pivot (client change d'avis)

⚠️ **Workflow rare mais critique**. Protocole **9 étapes** (orchestré par `/pivot`) :

```
1. cadrage/reunions/YYYY-MM-DD-pivot.md (capture réunion)
       ↓
2. cadrage/README.md (update : nouvelle direction)
       ↓
3. conception/research.md (append ## Pivot YYYY-MM-DD)
       ↓
4. conception/PRD.md (version bump v1.0 → v2.0)
       ↓
5. conception/tasks.md (refonte : ## Phase X — Refonte v2)
       ↓
6. ROADMAP.md (nouvelle section v2 dashboard)
       ↓
7. Si pivot technique : /adr cadrage "Pivot stack" (supersede les anciens ADRs)
       ↓
8. /lecon cadrage "Pourquoi le pivot" (status 🆕 new pour review post-mortem)
       ↓
9. /handoff (snapshot HANDOFF.md : nouvelle direction + next steps)
```

→ Tu peux déléguer ce workflow complet à l'agent `doc-maintainer` (Task tool).

## 📜 Quand créer un ADR (cf section `/adr` plus bas pour comment)

**Règle courte** : décision **cross-feature** OU qui **survit à la feature** → ADR global (`/adr <scope> "<titre>"`). Décision **locale à une feature** → section `## Décisions` dans `specs/00X/plan.md` (pas d'ADR).

→ **Critères détaillés (OUI/NON), 5 scopes, naming** = source unique dans [.claude/rules/template-maintenance.md § Convention ADR](.claude/rules/template-maintenance.md). Le « comment » (capture / supersede / deprecate / list) → section `/adr` ci-dessous.

## 📝 Workflow leçons (`/lecon`)

Skill unifié avec 4 sous-modes pour gérer tout le cycle de vie d'une leçon :

```bash
# Capture (défaut)
/lecon mvp "Notion rate limit"

# Promotion vers ADR ou rule (après review)
/lecon promote 2026-05-24
/lecon promote 2026-05-24 adr      # force destination
/lecon promote 2026-05-24 rule

# Discard (pas pertinent finalement)
/lecon discard 2026-05-24 "Résolu par mise à jour SDK"

# Archive (batch des stables > 3 mois)
/lecon archive
```

### Cycle de vie

```
   /lecon mvp "Notion rate limit"
       ↓
   🆕 new
       ↓ (review hebdo /doc-health → /lecon promote)
       ├─► 📜 → ADR-NNNN  (créé via /adr auto)
       ├─► 🔧 → rule       (créé dans .claude/rules/)
       ├─► 🧠 memory only  (laissé à auto-memory)
       └─► ❌ discarded    (via /lecon discard)
       ↓ (> 3 mois post-promotion stable)
   📦 archived  (via /lecon archive)
```

**Quand promouvoir ?**

- Pattern apparu **2+ fois** dans le projet → 🔧 rule
- Décision **cross-feature** ou **structurante** → 📜 ADR
- Pattern technique **mineur, contextuel** → 🧠 memory only
- Idée erronée → ❌ discarded

Détection auto : `/doc-health` flag les `🆕 new` > 14j.

## 💡 Workflow idées (`/idee`)

Skill unifié avec 4 sous-modes (symétrique à `/lecon`) :

```bash
# Capture (défaut) — crée fichier daté
/idee "Sync inverse Notion → Prestashop"

# Promotion vers spec (déclenche /spec)
/idee promote 2026-05-22

# Discard (abandonné)
/idee discard 2026-05-22 "Trop coûteux"

# Archive (batch des stables > 3 mois)
/idee archive
```

### Cycle de vie

```
   /idee "<titre>"
       ↓
   💡 Backlog (fichier idees/YYYY-MM-DD-titre.md créé)
       ↓ (review : valeur claire + effort acceptable)
       ├─► ✅ Promu en spec 00X  (via /idee promote, déclenche /spec auto)
       └─► ❌ Abandonné          (via /idee discard)
       ↓ (post-décision, > 3 mois)
   📦 archived/                  (via /idee archive)
```

**Important** : `idees/` = brainstorm **INTERNE** (toi). Ne pas confondre avec `cadrage/` = input **EXTERNE** (client).

Détection auto : `/doc-health` étape 9 flag les idées sans décision > 30j.

## 📜 Workflow ADRs (`/adr`)

Skill unifié avec 4 sous-modes :

```bash
# Capture (défaut)
/adr mvp "Stack BDD : Postgres vs SQLite"

# Supersede explicite (remplace ADR-0003)
/adr supersede 0003 mvp "Nouvelle stack httpx"

# Deprecate (marque comme à éviter, pas remplacé)
/adr deprecate 0005 "API tierce dépréciée"

# Lister (avec filtre optionnel)
/adr list
/adr list mvp        # filtre scope
/adr list accepted   # filtre status
```

### Pattern supersede

Un ADR est **immuable**. Si décision change :

1. `/adr supersede <NN> <scope> "<titre>"` (orchestration auto)
2. Le skill :
   - Crée le nouvel ADR avec `supersedes: <NN>`
   - Update l'ancien : `status: superseded` + `superseded_by: <new NN>`
   - Update `adr/README.md` : déplace ancien vers section "archived / superseded"
   - Append CHANGELOG section `Decided`

### Pattern deprecate (vs supersede)

- **supersede** : décision remplacée par une autre (avec lien)
- **deprecate** : décision encore là mais on n'élargit plus l'usage (pas de remplaçant)

```

→ Tu peux déléguer à l'agent `doc-maintainer` (Task tool).

## 🤖 Agent doc-maintainer

L'agent `doc-maintainer` est le **cerveau** invocable via Task tool. Il fait ce que les skills font, mais en **mode batch** + **scan auto** + **propose tous les diffs en une fois**.

### Quand préférer l'agent vs un skill

| Tu veux                                              | Préfère                  |
| ---------------------------------------------------- | ------------------------ |
| 1 action ciblée rapide (< 1 min)                     | Skill (`/handoff`, etc.) |
| Workflow complet (HANDOFF + ROADMAP + ADRs en batch) | Agent `doc-maintainer`   |
| Pivot client (9 étapes synchronisées)                | Agent                    |
| Audit + actions (vs juste audit)                     | Agent                    |
| Promotion multiple lecons → ADRs en une passe        | Agent                    |

### Comment l'invoquer

```

Lance l'agent doc-maintainer pour faire l'audit complet du projet et proposer toutes les MAJ.

````

(Claude utilisera le Task tool automatiquement)

### Règles de l'agent

- **JAMAIS d'overwrite silencieux** : toujours diff par diff
- **Ton concis**, factuel
- **Dates ISO** (YYYY-MM-DD)
- **Préserve les sections custom** de l'user (heuristique : non-templated → ne pas toucher)

## 🧑‍🤝‍🧑 Agent teams — déléguer à une équipe visible (tmux)

Le template est **câblé** pour les agent teams natifs : `settings.json` porte le flag
(`env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`) et `teammateMode: "tmux"` (chaque teammate
dans son pane). Le skill `/agent-teams:team`, les rôles d'exécution (`worker`/`front-end`/
`back-end`/`tester`) et le hook de trace viennent du **plugin `agent-teams`**
(`/plugin install agent-teams@claude-setup`). Prérequis : `tmux` dans le PATH. ⚠️ Split panes non supportés dans le terminal
VS Code / Windows Terminal — lance `claude` depuis un vrai terminal, ou passe
`teammateMode: "in-process"` pour tout garder dans le terminal courant (moins visible).

```
/plugin install agent-teams@claude-setup   # une fois (marketplace kurt83340/claude-Setup)
/agent-teams:team 001-erp-connector
```

Le lead propose un **plan d'équipe** (rôles préconfigurés `worker`/`front-end`/`back-end`/
`tester`/`reviewer` ou agents ad-hoc, 1 worktree par codeur, topologie de communication),
attend ta **validation**, spawne, suit (task list native + rapports SendMessage +
`.claude/.cache/team-progress.log`), merge, **débriefe la mémoire** et clôt proprement.

**Cycle de vie** : un teammate spawné par le lead de sa propre initiative est fermé par lui à
la clôture (lead-owned) ; un teammate que TU as demandé **persiste** — seul toi décides de le
fermer (user-owned). **Topologie** : par défaut chaque teammate ne parle qu'au lead
(hub-and-spoke) ; le mesh (teammates qui s'écrivent entre eux) est opt-in, scopé, décidé au spawn.

**Sessions sans prompts (sandbox uniquement)** : les teammates **héritent du mode de
permission du lead** au spawn → un seul levier. Soit le flag ponctuel
(`tmux new -s <projet> 'claude --resume --dangerously-skip-permissions'`), soit persistant
dans `.claude/settings.local.json` (non versionné) :
`{ "permissions": { "defaultMode": "bypassPermissions" } }`. Les règles `deny` (rm -rf,
`.env`…) restent appliquées. ⚠️ À réserver aux bacs à essai — sur un projet client, garde le
mode normal (les `allow`/`ask` du template existent pour ça).

→ Protocole complet (source unique) : [.claude/rules/agent-teams.md](.claude/rules/agent-teams.md).

## 🤖 Comprendre les hooks automatiques

| Hook                       | Quand ça se déclenche         | Ce que ça fait                            |
| -------------------------- | ----------------------------- | ----------------------------------------- |
| `PreCompact`               | Avant compaction du contexte  | Snapshot dans `.claude/.cache/` (non-versionné) + marker `/tmp/`      |
| `SessionStart(compact)`    | Reprise après compaction      | Re-inject le snapshot                     |
| `SessionEnd`               | À CHAQUE fin de session       | Filet « n'oublie rien » : snapshot d'état dans `.claude/.cache/` |
| `SessionStart(startup)`    | Nouveau démarrage             | Injecte le filet fin-de-session s'il est plus frais que HANDOFF.md, puis le consomme |
| `PreToolUse(Edit\|Write)`  | Avant Edit/Write fichier code | Réinjecte les règles de couplage + gotchas (non-déductibles) |
| `PostToolUse(Edit\|Write)` | Après Edit/Write fichier      | Détecte API_KEY/deploy/RGPD → flag growth |
| `Stop`                     | Fin de tour Claude            | Rappel `/handoff` si HANDOFF > 24h        |
| `TaskCreated`/`TaskCompleted`/`TeammateIdle` | Événements d'équipe (plugin `agent-teams`) | Trace JSON dans `.claude/.cache/team-progress.log` |

**Tous non-bloquants** : si un hook échoue, Claude continue.

**Debug** : `claude --debug` pour voir les hooks en action.

## 📊 Matrice "Quand créer un nouveau fichier ?"

**Règle d'or** : crée à la demande, JAMAIS préventivement.

→ **Matrice complète (trigger → fichier)** = source unique dans [.claude/rules/template-maintenance.md § Quand créer un nouveau fichier ?](.claude/rules/template-maintenance.md). Couvre ACCESS, RUNBOOK, ADR vs `plan.md`, GLOSSARY, specs, idées, leçons, code-map, stack, cadrage (documents / réunions / tickets) et diagrammes.

## 🎨 Convention diagrammes (3 formats)

→ **Source unique** (ASCII inline / Excalidraw+SVG / PNG, + règle « commit source ET export ») : [.claude/rules/template-maintenance.md § Convention diagrammes](.claude/rules/template-maintenance.md).

**Où placer** : simple → inline dans le .md (PRD, ARCHITECTURE, spec.md, plan.md) ; gros / éditable → dossier `diagrams/` local (`cadrage/diagrams/`, `conception/diagrams/`, `specs/00X/diagrams/`).

## 📛 Conventions de naming

→ **Source unique** (specs `00X`, ADR `00XX-<scope>-<titre>`, réunions/sources/idées datées ISO, leçons, tags git) : [.claude/rules/template-maintenance.md § Conventions de naming](.claude/rules/template-maintenance.md).

## 🚦 Conventions de statut

- **ROADMAP** (`[ ]` / `[~]` / `[x]`) → [.claude/rules/template-maintenance.md § Conventions de statut](.claude/rules/template-maintenance.md).
- **ADR** (`proposed` / `accepted` / `deprecated` / `superseded`) → [§ Convention ADR](.claude/rules/template-maintenance.md) (frontmatter YAML).
- **Leçons** / **Idées** : statuts définis dans leurs workflows ci-dessus (§ Workflow leçons `/lecon`, § Workflow idées `/idee`) — source unique.

## 🔐 Permissions (`settings.json`)

3 niveaux dans `.claude/settings.json` :

```json
{
  "permissions": {
    "allow": [...],   // exécuté sans demander
    "ask": [...],     // demande confirmation à chaque fois
    "deny": [...]     // refus systématique
  }
}
````

**Defaults du template** :

- `allow` : pytest, ruff, mypy, alembic, git status/log/diff/add/commit/tag, uv, npm, find, grep, Read/Edit/Write dans `.claude/docs/` et `src/`
- `ask` : `git push`, `git reset`, `alembic downgrade`, `./scripts/deploy`, `Read(./.env.*)` — **filet fail-closed** : tout `.env.*` non listé en deny (`.env.prod`, `.env.dev`…) déclenche un prompt au lieu d'être lisible en silence ; `.env.example` reste lisible après 1 confirmation
- `deny` : `rm -rf`, `.env` / `.env.local` / `.env.*.local` / `.env.{development,staging,production,test}`, `secrets.*`, `ACCESS.md`

**Customiser par projet** : édite `.claude/settings.json` pour ajouter tes commandes spécifiques (ex: `n8n:*`, `docker compose:*`).

## 📁 Organisation skills / agents

Skills/agents sont **à plat** dans leur dossier respectif. Claude Code scanne `.claude/skills/<nom>/SKILL.md` à **1 niveau seulement** (cf. [issue #18192](https://github.com/anthropics/claude-code/issues/18192) — feature request OPEN pour discovery récursive).

> ℹ️ **Plus de dossier `commands/`** : les custom commands ont fusionné avec les skills (même moteur,
> doc officielle : "Skills are recommended"). Le template n'utilise plus que le format skill.
> Source : [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).

```
.claude/
├── skills/
│   ├── handoff/SKILL.md         → /handoff
│   ├── spec/SKILL.md            → /spec
│   ├── feature-done/SKILL.md
│   ├── adr/SKILL.md
│   ├── deploy/SKILL.md          → /deploy (skill projet ; stacks n8n/BDD = plugins)
│   ├── ...
│   └── README.md
│
└── agents/
    ├── doc-maintainer.md        → invocable via Task tool
    └── README.md
```

### Règle clé : invocation = **nom du dossier**

```yaml
# .claude/skills/handoff/SKILL.md   ← le dossier "handoff" détermine /handoff
---
name: handoff # ← label d'affichage uniquement (ne change PAS l'invocation)
description: ...
---
```

→ C'est le **nom du dossier** qui fait le `/nom`. Convention : faire matcher dossier et `name:`
pour la lisibilité. (Exception : SKILL.md à la racine d'un plugin, où `name:` compte.)

### Pour grouper des skills par thème

Pas de namespace par sous-dossier en 2026. **2 vraies options** :

| Approche    | Exemple                              | Quand                                                                 |
| ----------- | ------------------------------------ | --------------------------------------------------------------------- |
| **Préfixe** | `n8n-deploy`, `n8n-test`, `n8n-lint` | Usage perso, pas de distribution                                      |
| **Plugin**  | `<plugin>/skills/<skill>/SKILL.md`   | Tu veux distribuer/partager, namespacing officiel `/<plugin>:<skill>` |

### Conflits de noms

Tous les skills sont dans le même espace de noms (`.claude/skills/`, `~/.claude/skills/`, plugins). Si collision → Claude en utilise UN (ordre alphabétique). Solution : renomme le dossier + `name:` du moins prioritaire.

Docs : voir `.claude/skills/README.md` et `.claude/agents/README.md`.

## 🛠️ Customisation

### Désactiver un hook

Édite `.claude/settings.json` et retire/vide la section concernée. Ex pour désactiver le rappel HANDOFF :

```json
"Stop": []
```

### Adapter un skill

Édite directement le `.claude/skills/<nom>/SKILL.md` (ex: `.claude/skills/handoff/SKILL.md`). Le frontmatter `allowed-tools` contrôle ce que Claude peut faire.

### Ajouter un nouveau skill (custom)

```bash
mkdir -p .claude/skills/mon-skill
cat > .claude/skills/mon-skill/SKILL.md <<'EOF'
---
name: mon-skill
description: Description claire pour que Claude sache quand l'invoquer
allowed-tools: Read, Write, Bash(...)
---

# Body du skill (instructions à Claude)
EOF
```

→ **Invocation** : `/mon-skill`. Le `name:` doit matcher le nom du dossier.

### Ajouter des skills depuis ailleurs (GitHub, MCP, autres repos)

Copie chaque skill directement dans `.claude/skills/<nom>/`. **Pas de sous-dossier de regroupement** (Claude Code ne scanne pas récursivement). Pour identifier la provenance sans sous-dossier : préfixe le nom (ex: `n8n-deploy`, `n8n-test`).

⚠️ **Conflits de noms** : tout est dans le même espace de noms (`.claude/skills/`, `~/.claude/skills/`, plugins). Si collision → Claude en utilise un (alphabétique). Rename le dossier + `name:` du moins prioritaire.

### Désactiver un skill (sans le supprimer)

Frontmatter : `disable-model-invocation: true` (Claude ne le suggérera plus, mais `/skill-name` manuel marche encore).

### Ajouter une slash command projet

Les « custom commands » (`.claude/commands/*.md`) ont **fusionné avec les skills** — même moteur,
même invocation, et la doc officielle recommande le format skill. Pour ajouter un `/deploy` :
voir « Ajouter un nouveau skill (custom) » ci-dessus (`mkdir -p .claude/skills/deploy` + SKILL.md).

⚠️ Pour une action sensible (deploy, push prod), ajoute `disable-model-invocation: true` au
frontmatter → invocation **uniquement** via `/deploy`, jamais déclenchée par Claude tout seul.

## ❌ Anti-patterns à éviter

- ❌ Créer un fichier "au cas où" (= ça pourrit)
- ❌ Mélanger `cadrage/` (input externe) et `idees/` (input interne)
- ❌ **Modifier un ADR passé** (créer un nouveau qui le supersede)
- ❌ Mettre des credentials dans le repo (`.env` est gitignored, valeurs ailleurs)
- ❌ Bug log séparé (tout va dans CHANGELOG)
- ❌ Skip le `/handoff` en fin de session (= perte de contexte garantie)
- ❌ Créer RUNBOOK avant la première mise en prod (= ça pourrit)
- ❌ Créer STAKEHOLDERS.md si < 5 personnes (= dans cadrage/README suffit)
- ❌ Cocher tasks `[x]` sans vérifier le DoD
- ❌ Promouvoir trop d'ADRs (décision locale = `## Décisions` dans plan.md, pas ADR)
- ❌ ADR sans frontmatter YAML (illisible machine, rate les audits doc-health)
- ❌ Skip `chmod +x .claude/hooks/*` au setup (= hooks bloquent)

## ✅ Bonnes pratiques

- ✅ Lire HANDOFF.md au démarrage de chaque session
- ✅ `/handoff` à la fin de chaque session
- ✅ Numéroter spec/ADR continûment (jamais de reset)
- ✅ Dater les fichiers de `idees/`, `cadrage/reunions/`, `cadrage/documents/`
- ✅ Référencer les ADRs depuis les specs concernées
- ✅ MAJ ROADMAP **à chaque** changement d'état de feature
- ✅ Garder le `CLAUDE.md` racine court & centré projet (< 60 lignes) ; template & skills → `.claude/CLAUDE.md` ; détail → `@.claude/rules/*.md`
- ✅ Préférer un ADR à un long commit message pour les décisions structurantes
- ✅ Diff par diff (l'agent doc-maintainer le fait par défaut)

## 🐛 Troubleshooting

### Les skills n'apparaissent pas dans `/skills`

- Vérifier que le fichier est `SKILL.md` (majuscules) dans `.claude/skills/<nom>/` (à plat, 1 niveau seulement — Claude Code ne scanne pas récursivement, [issue #18192](https://github.com/anthropics/claude-code/issues/18192))
- Frontmatter valide (`name:` + `description:` minimum)
- Le `name:` du frontmatter doit matcher le nom du dossier
- Relancer Claude Code (les skills sont scannés au démarrage)
- Lancer `/doctor` pour voir les erreurs

### Un hook ne se déclenche pas

- Vérifier le chemin du script dans `settings.json` (utiliser `${CLAUDE_PROJECT_DIR}`)
- Vérifier que le script est **exécutable** : `chmod +x .claude/hooks/*.py *.sh`
- Vérifier le `matcher` (regex `Edit|Write` est correct, pas `Edit\\|Write`)
- Lancer `claude --debug` et regarder les logs

### Le hook code-map injecte rien

- Vérifier que `.claude/docs/code-map.md` existe et contient au moins une des sections
  `## Règles de couplage`, `## Intention & décisions locales`, `## Gotchas`
- Le hook ne fonctionne que pour fichiers dans `/src/`, `/tests/`, `/lib/`, `/app/`

### `/init-from-template` ne marche pas

- Vérifier que tu es dans un projet copié (pas dans le template original)
- Lancer manuellement : `python3 .claude/skills/init-from-template/scripts/render.py --list-placeholders`

### Auto-memory ne sauvegarde pas

- Vérifier `settings.json` : `"autoMemoryEnabled": true`
- Vérifier que `~/.claude/projects/<encoded-path>/memory/` est créé
- Auto-memory ne sauvegarde que tous les ~5-10 messages (pas chaque turn)

### Agent doc-maintainer pas trouvé

- Vérifier `.claude/agents/doc-maintainer.md` existe (à plat dans `agents/`, pas de sous-dossier)
- Frontmatter valide (`name`, `description`, `tools`, `model: inherit`)
- Invoquer via Task tool, pas `/doc-maintainer` (les agents ne sont pas des slash commands)

## 📚 Skills built-in Claude utiles

| Skill                | Pour quoi                                                           |
| -------------------- | ------------------------------------------------------------------- |
| `/security-review`   | Avant chaque push prod (vérif sécurité changes courants)            |
| `/code-review`       | Avant merge d'une feature complexe                                  |
| `/resume`            | Reprendre session précise (fidélité 100%)                           |
| `/loop 10m /handoff` | Auto-update HANDOFF toutes les 10 min en session longue (optionnel) |
| `/init`              | ❌ **NE PAS utiliser** (ce template a déjà CLAUDE.md)               |
| `/compact`           | Force la compaction manuelle (rare, sinon auto à ~90%)              |
| `/clear`             | Reset complet du contexte (perd auto-memory volatile)               |
| `/doctor`            | Diagnostic des skills/hooks/agents                                  |

## 📚 Aller plus loin

| Fichier                                                                        | Pour quoi                                                       |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| [STRUCTURE.md](STRUCTURE.md)                                                   | Convention 2026 complète (arborescence, naming, patterns)       |
| [CLAUDE.md](CLAUDE.md)                                                         | Index **projet** : résumé + nav doc + conventions               |
| [.claude/CLAUDE.md](.claude/CLAUDE.md)                                         | Index **template** : skills, workflow, agent                    |
| [.claude/rules/template-maintenance.md](.claude/rules/template-maintenance.md) | Méta-doc : 3 layers mémoire, fichiers vivants, conventions      |
| [.claude/docs/adr/README.md](.claude/docs/adr/README.md)                       | Convention ADRs détaillée                                       |
| [.claude/docs/conception/README.md](.claude/docs/conception/README.md)         | Pattern mirror macro/micro                                      |
| [.claude/docs/cadrage/README.md](.claude/docs/cadrage/README.md)               | Template cadrage initial                                        |
| [EXAMPLES/acme-sync-erp-notion-docs/](EXAMPLES/acme-sync-erp-notion-docs/)     | Exemple rempli (repo template ; exclu de ton projet par l'init) |

## 🎯 Philosophie

**3 principes** :

1. **Documenter au fur et à mesure**, pas à la fin (sinon tu oublies)
2. **Laisser les skills faire le boulot répétitif** (handoff, feature-done, doc-health, adr)
3. **Faire confiance aux hooks** pour ce qui doit toujours se passer (snapshot, code-map injection, growth detection)

**Anti-pattern** : essayer de tout faire manuellement → tu vas te démotiver. Le template existe pour automatiser l'ennuyeux.

**Rappel** : le but du template c'est qu'**en 30 secondes**, n'importe quelle session démarre avec tout le contexte projet auto-chargé. **HANDOFF.md** est la clé de voûte.

**3 layers** = redondance saine. Si auto-memory perd un truc, HANDOFF rattrape. Si HANDOFF est stale, le code parle. Si le code est obscur, CLAUDE.md + rules cadrent.
