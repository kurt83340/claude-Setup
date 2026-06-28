# USAGE — Comment utiliser ce template

> Guide pratique : skills + agent + hooks + workflows au quotidien.

---

## 🚀 Setup d'un nouveau projet (à lire EN PREMIER)

### Procédure complète (6 étapes, ~5 min)

```bash
# 1. Copier le template (exclut EXAMPLES et test pour pas polluer)
rsync -av --exclude='EXAMPLES/' --exclude='test/' --exclude='.git/' \
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
4. **Lancer `cleanup-for-type.py`** selon le type choisi (adapte le template)
5. **Copier auto depuis EXAMPLES** si pertinent (ex: type `automation-n8n` → copie les skills `skills-n8n/` dans `.claude/skills/`)
6. **Te proposer le commit initial** : `feat: init projet <nom> depuis template`

### Les 5 types de projet (impact sur cleanup)

| Type             | Impact   | Skills restants             | Use case                         |
| ---------------- | -------- | --------------------------- | -------------------------------- |
| `script-jetable` | **-80%** | 3 (handoff, lecon, init)    | 1-shot Python, < 1 jour          |
| `python-app`     | léger    | 11 (tous)                   | App Python (FastAPI, scripts...) |
| `web-app`        | léger    | 11 (tous)                   | Next.js, React, etc.             |
| `automation-n8n` | léger    | 11 + skills n8n copiés      | Workflow n8n + helpers Python    |
| `bdd-migration`  | léger    | 11 (db-migration prominent) | Migration BDD avec Alembic       |

### Vérification post-init

```bash
# 1. Tous les CORE placeholders sont substitués ?
python3 .claude/skills/init-from-template/scripts/render.py --check
# → ✅ "Tous les placeholders CORE sont substitués"

# 2. Premier commit du projet rempli
git add .
git commit -m "feat: init projet <nom> depuis template"
```

### Prochaines étapes après init

1. **Remplir `cadrage/README.md`** (verbatim demande client + interlocuteurs)
2. **Planifier le kickoff** → archiver compte-rendu dans `cadrage/reunions/`
3. **Quand brief mûr** → remplir `conception/PRD.md`
4. **Quand archi décidée** → `conception/ARCHITECTURE.md`
5. **Démarrer 1ère feature** : `/spec "<titre>"`

### Troubleshooting init

- **`chmod: No such file or directory`** → tu es au mauvais endroit, vérifie `cd`
- **`render.py: 0 fichiers à scanner`** → le rsync n'a rien copié (vérifie source)
- **`/init-from-template` pas trouvé** → relance `claude` (skills scannés au démarrage)
- **CORE manquants après render** → ajoute-les au vars.json et relance

---

## 🧠 Comprendre AVANT d'utiliser : les 3 layers de mémoire

Claude Code 2.1+ a 3 couches de mémoire qui se complètent. **Ne les confonds pas.**

| Layer           | Fichier                                                                      | Qui écrit              | Survit à quoi ?              | Versionné git ?        |
| --------------- | ---------------------------------------------------------------------------- | ---------------------- | ---------------------------- | ---------------------- |
| **1. Stable**   | `CLAUDE.md` (projet) + `.claude/CLAUDE.md` (template) + `.claude/rules/*.md` | Toi (humain)           | Toujours                     | ✅ Oui                 |
| **2. Patterns** | `~/.claude/projects/<projet>/memory/MEMORY.md`                               | Claude (auto)          | Sessions, compaction, /clear | ❌ Non (machine-local) |
| **3. État**     | `.claude/docs/HANDOFF.md`                                                    | `/handoff` skill + toi | Sessions, compaction         | ✅ Oui                 |

**Quoi mettre où** :

- Règles **invariantes** du projet → `.claude/rules/*.md`
- Patterns **appris** automatiquement → MEMORY.md (Claude le gère, tu ne touches pas)
- **État volatile** (où j'en suis, blockers, next) → HANDOFF.md (court, narratif)

**`/resume` vs HANDOFF.md** :

- `/resume` = built-in Claude, garde 100% du contexte conversation précédente (idéal pour reprendre dans la même journée)
- `HANDOFF.md` = sert quand : tu changes de machine, tu clones le repo ailleurs, tu partages avec un collègue, ou tu démarres une session fraîche après plusieurs jours

→ Les deux sont **complémentaires**. HANDOFF n'est pas obsolète à cause de `/resume`.

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

Audit complet (12 étapes) qui scanne sans modifier :

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

Rapport généré → tu suis les actions par priorité.

## 📋 Cheat sheet — Quand utiliser quoi

| Situation                                  | Skill / Action                                      |
| ------------------------------------------ | --------------------------------------------------- |
| Nouveau projet                             | `/init-from-template`                               |
| Démarrer une feature                       | `/spec "<titre>"` (scaffold 4 fichiers + ROADMAP)   |
| Fin de session                             | `/handoff`                                          |
| Feature livrée                             | `/feature-done <spec-id>`                           |
| Décision tech structurante (cross-feature) | `/adr <scope> "<titre>"`                            |
| Décision tech locale à 1 feature           | Section `## Décisions` dans `specs/00X/plan.md`     |
| Bug/observation à noter rapidement         | `/lecon <scope> "<titre>"`                          |
| Idée perso à capturer                      | `/idee "<titre>"`                                   |
| Refacto majeur sur le code                 | `/codemap`                                          |
| Audit hebdo                                | `/doc-health`                                       |
| BDD migration (Alembic)                    | `/db-migration`                                     |
| Workflow batch (HANDOFF + ROADMAP + ADRs)  | Task `doc-maintainer` (agent)                       |
| Pivot client                               | `/pivot "<raison>"` (workflow 7 étapes orchestrées) |
| Promotion leçon → ADR / rule               | `/lecon promote <date>`                             |
| Promotion idée → spec                      | `/idee promote <date>`                              |
| Supersede un ADR                           | `/adr supersede <NN> <scope> "<titre>"`             |
| Lister tous les ADRs                       | `/adr list [scope]`                                 |
| Archiver leçons/idées vieilles             | `/lecon archive` ou `/idee archive`                 |
| Reprendre exactement où on en était        | `/resume` (built-in Claude)                         |
| Compaction context (auto)                  | RIEN — hooks gèrent                                 |
| Édition fichier code (auto)                | RIEN — hook injecte code-map context                |
| Mention API_KEY/deploy dans code (auto)    | RIEN — hook flag dans growth-suggestions            |

## 🔁 Workflow type pour une feature complète

```
1. Lire ROADMAP.md → choisir la prochaine feature
       ↓
2. /spec "Export PDF"
   → scaffold auto : conception/specs/004-export-pdf/{research,spec,plan,tasks}.md
   → update ROADMAP.md auto
       ↓
3. Remplir les 4 fichiers générés (substituer les {{...}} CONTENT placeholders)
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

⚠️ **Workflow rare mais critique**. Protocole 7 étapes :

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
```

→ Tu peux déléguer ce workflow complet à l'agent `doc-maintainer` (Task tool).

## 📜 Quand créer un ADR (cf section `/adr` plus bas pour comment)

✅ **OUI** :

- Choix de stack (langage, framework, BDD, orchestration)
- Choix d'archi (monolithe vs microservices, REST vs GraphQL)
- Conventions structurantes (auth JWT vs sessions, async Celery)
- Décisions sécurité (où stocker les secrets)
- Migration BDD majeure
- **Cross-feature** : impacte plusieurs features
- Décision qui **survit à la feature**

❌ **NON — utiliser `## Décisions` dans `plan.md` de la spec** :

- Choix de lib pour parser CSV dans UNE feature
- Convention de nommage locale à une feature
- Refacto interne d'un module
- Fix de bug

**Règle de promotion** : décision feature **survit** OU **référencée ailleurs** → promouvoir ADR global.

5 scopes : `cadrage` | `mvp` | `feature-00X` | `infra` | `operations`
Naming : `00XX-<scope>-<titre-kebab>.md` (séquentiel sans reset).

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
| Pivot client (7 étapes synchronisées)                | Agent                    |
| Audit + actions (vs juste audit)                     | Agent                    |
| Promotion multiple lecons → ADRs en une passe        | Agent                    |

### Comment l'invoquer

```

Lance l'agent doc-maintainer pour faire l'audit complet du projet et proposer toutes les MAJ.

```

(Claude utilisera le Task tool automatiquement)

### Règles de l'agent

- **JAMAIS d'overwrite silencieux** : toujours diff par diff
- **Ton concis**, factuel
- **Dates ISO** (YYYY-MM-DD)
- **Préserve les sections custom** de l'user (heuristique : non-templated → ne pas toucher)

## 🤖 Comprendre les hooks automatiques

| Hook                       | Quand ça se déclenche         | Ce que ça fait                            |
| -------------------------- | ----------------------------- | ----------------------------------------- |
| `PreCompact`               | Avant compaction du contexte  | Snapshot dans `.claude/.cache/` (non-versionné) + marker `/tmp/`      |
| `SessionStart(compact)`    | Reprise après compaction      | Re-inject le snapshot                     |
| `PreToolUse(Edit\|Write)`  | Avant Edit/Write fichier code | Réinjecte les règles de couplage + gotchas (non-déductibles) |
| `PostToolUse(Edit\|Write)` | Après Edit/Write fichier      | Détecte API_KEY/deploy/RGPD → flag growth |
| `Stop`                     | Fin de tour Claude            | Rappel `/handoff` si HANDOFF > 24h        |

**Tous non-bloquants** : si un hook échoue, Claude continue.

**Debug** : `claude --debug` pour voir les hooks en action.

## 📊 Matrice "Quand créer un nouveau fichier ?"

**Règle d'or** : crée à la demande, JAMAIS préventivement.

| Trigger                                                         | Fichier à créer                                                            |
| --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| User mentionne credentials/API/OAuth → pas d'ACCESS.md riche    | `.claude/docs/ACCESS.md`                                                   |
| User parle de déploiement prod imminent                         | `.claude/docs/RUNBOOK.md`                                                  |
| Décision tech impacte plusieurs features OU survit à la feature | `/adr <scope> "<titre>"` → crée `.claude/docs/adr/00XX-<scope>-<titre>.md` |
| Décision tech **locale à UNE feature**                          | Section `## Décisions` dans `specs/00X/plan.md` (PAS d'ADR séparé)         |
| > 3 références à un terme métier non documenté                  | Créer/enrichir `.claude/docs/GLOSSARY.md`                                  |
| Démarrage d'une feature                                         | `.claude/docs/conception/specs/00X-feature/{research,spec,plan,tasks}.md`  |
| Nouvelle idée perso pas mûre                                    | `.claude/docs/idees/YYYY-MM-DD-titre.md`                                   |
| Bug/pattern/observation à capturer                              | `/lecon <scope> "<titre>"` → append dans `lecons.md` (status 🆕 new)       |
| **Avant d'éditer un fichier de code**                           | **Vérifier les règles de couplage dans `code-map.md`** (rôle/imports : se lisent dans le code) |
| Nouvelle règle de couplage / contrainte d'archi / gotcha        | MAJ `.claude/docs/code-map.md` (ou `/codemap`) — pas de file-by-file        |
| Nouvelle lib Python / service tiers / LLM utilisé               | MAJ `.claude/docs/stack.md`                                                |
| Doc reçue du client                                             | `.claude/docs/cadrage/documents/YYYY-MM-DD-description.ext`                |
| Compte-rendu de réunion                                         | `.claude/docs/cadrage/reunions/YYYY-MM-DD-titre.md`                        |
| Ticket Jira/Linear/Asana reçu                                   | `.claude/docs/cadrage/tickets/TICKET-XXX-titre.md`                         |
| Pivot client                                                    | Voir [Workflow pivot](#-workflow-pivot-client-change-davis)                |
| Diagramme business simple                                       | Inline ASCII dans `cadrage/README.md`                                      |
| Diagramme business complexe                                     | `cadrage/diagrams/X.excalidraw` + export `.svg`                            |
| Diagramme technique simple                                      | Inline ASCII dans `conception/ARCHITECTURE.md`                             |
| Diagramme technique gros                                        | `conception/diagrams/X.excalidraw` + export `.svg`                         |
| Diagramme spécifique à une feature                              | Inline dans `specs/00X/plan.md` ou `specs/00X/diagrams/` (rare)            |

## 🎨 Convention diagrammes (3 formats)

| Format                       | Quand                                      | Claude-friendly ?         |
| ---------------------------- | ------------------------------------------ | ------------------------- |
| **ASCII inline** dans le .md | Default — diagrammes simples (flow, arbre) | ✅ Parfait                |
| **Excalidraw + export SVG**  | Diagrammes visuels complexes               | ⚠️ SVG via Read explicite |
| **PNG/JPG**                  | Screenshots, photos uniquement             | ⚠️ Pas fiable en 2026     |

**Règle d'or images** : commit **la SOURCE éditable + l'EXPORT SVG/PNG** côte à côte.

```

diagrams/
├── flow-X.excalidraw # source éditable (humain)
└── flow-X.svg # export (Claude + GitHub preview)

````

⚠️ `![](path.png)` dans un .md n'est PAS auto-suivi par Claude. Pour qu'il "voit" un diagramme image, il faut un Read explicite ou pointer vers un .md ASCII.

## 📛 Conventions de naming

| Type            | Format                                              | Exemple                                            |
| --------------- | --------------------------------------------------- | -------------------------------------------------- |
| Specs           | `00X-feature-name/` (séquentiel sans reset)         | `001-erp-connector/`, `002-notion-writer/`         |
| ADR             | `00XX-<scope>-<titre-kebab>.md` (séquentiel global) | `0007-mvp-stack-bdd.md`, `0008-infra-1password.md` |
| Réunions/pivots | `YYYY-MM-DD-titre.md`                               | `2026-05-20-kickoff.md`, `2026-06-12-pivot.md`     |
| Sources reçues  | `YYYY-MM-DD-description.ext`                        | `2026-05-15-rgpd-spec.pdf`                         |
| Idées perso     | `YYYY-MM-DD-titre-court.md`                         | `2026-05-22-sync-inverse.md`                       |
| Leçons          | Header `## YYYY-MM-DD — <titre>` dans `lecons.md`   | `## 2026-05-24 — Notion rate limit`                |
| Tags git        | `vYYYY.MM.DD-HHMM`                                  | `v2026.06.10-1430`                                 |

## 🚦 Conventions de statut

### ROADMAP

- `[ ]` = planifié, pas commencé
- `[~]` = en cours (mettre en **gras** pour visibilité)
- `[x]` = livré

### ADR (frontmatter)

- `proposed` = en discussion
- `accepted` = décidé, en vigueur
- `deprecated` = à éviter mais pas remplacé
- `superseded` = remplacé par un autre ADR (lien `superseded_by`)

### Leçons

- `🆕 new` = observé, pas décidé (défaut)
- `📜 → ADR-00XX` = promu en ADR (avec lien)
- `🔧 → rule X` = promu en règle Claude (path)
- `🧠 → memory only` = laissé à auto-memory
- `❌ discarded` = pas pertinent
- `📦 archived` = fermé post-promotion stable

### Idées

- `💡 Backlog` = en attente
- `🔄 À promouvoir en spec`
- `💬 Discuter avec X`
- `✅ Promu en spec 00X — YYYY-MM-DD`
- `❌ Abandonné`

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
- `ask` : `git push`, `git reset`, `alembic downgrade`, `./scripts/deploy`
- `deny` : `rm -rf`, `Read(./.env)`, `Read(./.env.local)`

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
│   ├── n8n-push/SKILL.md        → /n8n-push (exemple stack, préfixé)
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

| Fichier                                                                        | Pour quoi                                                  |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| [STRUCTURE.md](STRUCTURE.md)                                                   | Convention 2026 complète (arborescence, naming, patterns)  |
| [CLAUDE.md](CLAUDE.md)                                                         | Index **projet** : résumé + nav doc + conventions          |
| [.claude/CLAUDE.md](.claude/CLAUDE.md)                                         | Index **template** : skills, workflow, agent               |
| [.claude/rules/template-maintenance.md](.claude/rules/template-maintenance.md) | Méta-doc : 3 layers mémoire, fichiers vivants, conventions |
| [.claude/docs/adr/README.md](.claude/docs/adr/README.md)                       | Convention ADRs détaillée                                  |
| [.claude/docs/conception/README.md](.claude/docs/conception/README.md)         | Pattern mirror macro/micro                                 |
| [.claude/docs/cadrage/README.md](.claude/docs/cadrage/README.md)               | Template cadrage initial                                   |
| [EXAMPLES/acme-sync-erp-notion-docs/](EXAMPLES/)                               | Exemple complet rempli (référence ACME)                    |

## 🎯 Philosophie

**3 principes** :

1. **Documenter au fur et à mesure**, pas à la fin (sinon tu oublies)
2. **Laisser les skills faire le boulot répétitif** (handoff, feature-done, doc-health, adr)
3. **Faire confiance aux hooks** pour ce qui doit toujours se passer (snapshot, code-map injection, growth detection)

**Anti-pattern** : essayer de tout faire manuellement → tu vas te démotiver. Le template existe pour automatiser l'ennuyeux.

**Rappel** : le but du template c'est qu'**en 30 secondes**, n'importe quelle session démarre avec tout le contexte projet auto-chargé. **HANDOFF.md** est la clé de voûte.

**3 layers** = redondance saine. Si auto-memory perd un truc, HANDOFF rattrape. Si HANDOFF est stale, le code parle. Si le code est obscur, CLAUDE.md + rules cadrent.
