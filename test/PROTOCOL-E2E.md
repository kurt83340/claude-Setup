# Protocole E2E — tester le template sur un projet jetable

> **Ce que les suites mécaniques ne couvrent pas.** `test_*.py` + la CI gardent les scripts,
> hooks et manifests. CE protocole teste l'**agentique** : une session Claude qui suit les
> skills produit-elle les bons artefacts, et les garde-fous refusent-ils ce qu'ils doivent
> refuser ? À rejouer **à chaque version majeure** (successeur méthodologique de
> `TEST-REPORT.md` — la boucle qui avait produit les fixes F1→F10).
>
> Étalonné le 2026-07-07 sur v0.17.0 (fixture « caisse », rapport en fin de fichier).

## Verdicts

- **PASS** — artefacts conformes aux critères observables
- **PARTIEL** — artefact produit mais friction notée (→ F-note)
- **FAIL** — critère non atteint
- **N-T** — non testable headless → § Phase M (manuel assisté)

Toute friction = **F-note numérotée** en fin de rapport → candidate fix pour la version suivante.

## Prérequis

- Template à jour, **batterie CI locale verte** (sinon on teste du cassé)
- `python3`, `git`, `rsync` ; le jetable vit dans un dossier temporaire isolé (jamais dans un vrai projet)
- Phase M uniquement : `tmux` + session Claude interactive

## Fixture fil rouge « caisse »

Mini-app Python réaliste (les skills ont besoin de matière) :

```python
# src/caisse.py
TVA = 0.20

def total_ht(lignes):            # lignes = [(prix_unitaire, qte), ...]
    return sum(p * q for p, q in lignes)

def total_ttc(lignes, remise=0.0):
    # ⚠️ BUG DORMANT pour la Phase 6 — version buggée à activer :
    #   ht = total_ht(lignes) - remise        # remise soustraite en MONTANT ABSOLU
    # (⚠️ ne PAS utiliser « remise après TVA » comme bug : c'est mathématiquement
    # ÉQUIVALENT — commutativité — aucun test ne rougit. Friction F1 de l'étalonnage.)
    ht = total_ht(lignes) * (1 - remise)
    return round(ht * (1 + TVA), 2)
```

```python
# tests/test_caisse.py — 2 tests verts au départ
import sys, unittest
sys.path.insert(0, "src")
from caisse import total_ht, total_ttc

class TestCaisse(unittest.TestCase):
    def test_total_ht(self):
        self.assertEqual(total_ht([(10, 2), (5, 1)]), 25)
    def test_total_ttc_sans_remise(self):
        self.assertEqual(total_ttc([(10, 2), (5, 1)]), 30.0)
```

**Variante brownfield** (Phase 0bis) : la même app + un `README.md` maison, un `CLAUDE.md`
maison (2 lignes), un `.github/workflows/deploy.yml` maison, un historique git — pour
vérifier que l'adoption **ne détruit rien**.

---

## Phase 0 — Greenfield : init complet (× 5 types)

**Actions** : rsync documenté (USAGE §Setup) → `chmod +x hooks` → `git init` + snapshot →
`vars.json` (10 CORE) → `render.py --vars` → `--check` → `cleanup-for-type.py --type <t>` →
traçabilité version dans `stack.md` (si conservé par le profil) → commit init.
⚠️ **Rejouer pour CHAQUE `--type`** (`script-jetable`, `automation-n8n`, `python-app`,
`web-app`, `bdd-migration`) — cette étape est purement mécanique, un harnais scripté suffit
(boucle rsync→render→cleanup→verify-e2e ; le déroulé agentique complet reste sur UN type).

**PASS si** : 0 CORE restant (grep du périmètre substitué) · skills bootstrap absents ·
inventaires SANS skill mort (bootstrap + skills supprimés par le profil ; compte « N skills
cœur » recalé) · nav sans lien mort (pointeurs create-on-demand ACCESS/GLOSSARY/RUNBOOK
conservés) · allow-rules mortes purgées · `.claude/template-version` présent · ligne
`Template claude-Setup vX.Y.Z` dans `stack.md` (**sauf** `script-jetable` qui supprime
stack.md — la trace = `template-version` seul) · @-imports CLAUDE.md tous vivants (3 ;
1 en `script-jetable`, ROADMAP/code-map supprimés par le profil) · hooks exécutables.

## Phase 0bis — Brownfield : adoption

**Actions** : sur la fixture brownfield, rsync `--ignore-existing` (excludes documentés) →
render → `--check` → `cleanup --type python-app --brownfield` → étapes agentiques : merge
CLAUDE.md existant (≤3 @-imports au total), rétro-remplissage `stack.md` (+ version) et
`HANDOFF` (← git log).

**PASS si** : fichiers USER **intacts** (README, CLAUDE.md à lui, `.github/` à lui, code) ·
scaffold `.claude/` posé · **aucun strip** · permissions non purgées · skills bootstrap
encore là (retrait = Étape 5 d'adopt, manuel) · stack.md rétro-rempli.

## Phase 1 — Cadrage (+ piège bucket)

**Actions** : remplir `cadrage/README.md` (verbatim + interlocuteurs), 1 ticket
`cadrage/tickets/`, 1 réunion `cadrage/reunions/YYYY-MM-DD-*.md`. **Piège** : énoncer
« j'ai eu une idée perso : X » → doit finir dans `idees/YYYY-MM-DD-*.md`, PAS dans cadrage.

**PASS si** : nommage ISO respecté · distinction cadrage(externe)/idees(interne) respectée.

## Phase 2 — `/spec`

**PASS si** : `specs/001-<kebab>/` avec les 4 fichiers · 0 `{{SPEC_*}}` restant ·
ROADMAP a la ligne liée · numérotation démarre à 001.

## Phase 3 — `/conception` (calibrable en allégé : sans subagents)

**Actions** : contraintes chargées (code-map/ADR/leçons) → ≥2 options tracées dans
`research.md` → décision → `plan.md` avec points de vérification + **mode d'exécution
(TDD/standard) noté § Décisions** → `tasks.md` partitionné → trace de revue adverse.

**PASS si** : `plan.md § Décisions` non vide (mode présent) · `research.md` ≥2 options ·
tasks atomiques cochables.

## Phase 4 — `/feature` pipeline `tdd`

**PASS si** : auto-sélection du pipeline depuis `plan.md § Décisions` · tests écrits AVANT
le code et **ROUGES pour la bonne raison** · verts sans modification des tests · trace de
review adverse · DoD relu · gates respectés (pas d'étape sautée).

## Phase 5 — Cycle de vie des artefacts

**Actions** : `/lecon` capture puis `promote` → ADR · `/adr` capture puis `supersede` ·
`/idee` capture puis `promote` → spec 002.

**PASS si** : frontmatter/statuts corrects · **ADR ancien intact** hors champ status
(immuabilité) · index `adr/README.md` à jour (section superseded) · leçon promue marquée
`📜 → ADR-XXXX` · numérotation continue (002 après 001, pas de reset).

## Phase 6 — `/debug` (bug injecté)

**Actions** : activer le bug dormant de la fixture (remise soustraite en montant absolu), symptôme verbatim. Le bug DOIT faire rougir un test existant ou un test de repro écrit sur-le-champ.

**PASS si** : test de repro écrit et ROUGE **avant** tout fix · fix minimal (le diff ne
touche que la cause) · le test de repro RESTE dans la suite · leçon capturée · CHANGELOG
`### Fixed`.

## Phase 7 — `/feature-done` + `/pivot` (léger)

**PASS feature-done si** : ROADMAP `[x]` daté · CHANGELOG entry · HANDOFF à jour · idée
source archivée (`✅ Promu en spec 00X`).
**PASS pivot si** : réunion datée · `research.md` § Pivot daté · PRD v1→v2 · ROADMAP
section v2 · ADR si pivot technique.

## Phase 8 — `/doc-health` + `/codemap`

**PASS doc-health si** : le rapport reflète l'état RÉEL du jetable (leçons 🆕 restantes,
CORE=0, specs stalled…) et **ne modifie rien**.
**PASS codemap si** : règles de couplage + gotchas écrits · **aucun** file-by-file.

## Phase 9 — `/scaffold`

**Actions** : créer 1 skill projet bidon (mode skill).
**PASS si** : `name:` = dossier · ligne d'inventaire ajoutée dans `.claude/CLAUDE.md` ·
(si agent teammate testé : `SendMessage` dans tools).

## Phase 10 — `/handoff`

**PASS si** : HANDOFF réel (0 placeholder `{{ }}`) · sections Échecs tentés / Blocked /
Next remplies avec du contenu de la session · bloc **Continuation State** présent avec ses
5 clés (`Spec` / `Task` / `Fichiers en cours` / `Bloqué sur` / `Commande de reprise`).

## Phase B — Benchmarks de skills (`test/benchmarks/`)

Pour **chaque scénario** `test/benchmarks/<skill>/<cas>.md` (structure déjà validée en CI
par `test_skills.py` — ici on joue le COMPORTEMENT) :

1. Préparer le jetable selon `state` (frontmatter du scénario).
2. Jouer `input` dans la session de test.
3. Vérifier chaque `assert-contains` / `assert-not-contains` sur la sortie et les fichiers,
   puis les puces de « Attendu » une à une.

**PASS si** : toutes les assertions du scénario passent. Un scénario ⚠️/❌ = citer
l'assertion échouée dans le rapport. Les phases 2/8/10 couvrent déjà en partie les seeds
(`spec`, `doc-health`, `handoff`) — Phase B les rejoue sur l'état FINAL du jetable, ce qui
attrape les régressions d'état accumulé (numérotation, incohérences ROADMAP↔frontmatter).

## Phase E — Cas d'erreur (tester les REFUS)

| # | Provocation | Attendu |
|---|---|---|
| E1 | « Modifie l'ADR 0001 » (accepted) | Refus + proposition `supersede` |
| E2 | Déposer une idée perso dans `cadrage/` | Redirection vers `idees/` |
| E3 | Pipeline référençant un maillon absent | `/feature` le signale + propose l'alternative (pas d'échec silencieux) |
| E4 | `/feature-done` avec tasks non cochées | Demande de confirmation explicite |
| E5 | Committer HANDOFF « depuis un worktree teammate » | Refus (règle agent-teams) |

## Phase M — Manuel assisté (session interactive requise, N-T en headless)

| # | Quoi | Procédure |
|---|---|---|
| M1 | Auto-invocation par description | Dire « j'ai eu une idée : … » sans slash → `/idee` doit se déclencher |
| M2 | Hooks réels | éditer `src/` → injection code-map visible ; `touch -d '2 days ago' HANDOFF.md` + changements git → Stop reminder |
| M3 | Permissions | `rm -rf` → deny · `Read .env` → deny · `.env.example` → prompt ask |
| M4 | Plugins | `/plugin marketplace add` + install `agent-teams` → `/agent-teams:team` sur spec 002 (tmux) |
| M5 | Compaction | `/compact` → snapshot réinjecté (SessionStart compact) |

## Vérification finale scriptée

```bash
python3 <template>/test/verify-e2e.py --root <jetable>   # exit 0 = invariants OK
```

## Gabarit de rapport

```markdown
# Rapport E2E — vX.Y.Z — YYYY-MM-DD
| Phase | Verdict | Notes |
|---|---|---|
| 0 greenfield | PASS/… | |
| 0bis brownfield | | |
| 1..10, E, M | | |
Frictions : F1 … / F2 …
verify-e2e.py : N/N ✅
```

---

## Rapport d'étalonnage — v0.17.0, 2026-07-07 (fixture « caisse »)

| Phase | Verdict | Notes |
|---|---|---|
| 0 greenfield | **PASS** | 10/10 critères |
| 0bis brownfield | **PASS** (mécanique) | merges CLAUDE.md agentiques = spot-check |
| 1 cadrage + piège | **PASS** | idée correctement routée vers `idees/` |
| 2 /spec | **PASS** | |
| 3 /conception | **PASS** (allégé, sans subagents) | 2 options tracées, mode TDD noté |
| 4 /feature tdd | **PASS** | rouge→vert, tests non modifiés |
| 5 artefacts | **PASS** | supersede + promote OK, immuabilité respectée |
| 6 /debug | **PASS** (après F1) | 1er bug choisi était un non-bug (commutatif, 0 rouge) → fixture corrigée, rejoué : rouge `11.4 != 6.0` observé → fix minimal → vert |
| 7 feature-done + pivot | **PASS** (pivot léger) | |
| 8 doc-health + codemap | **PASS** | audit fidèle, 0 modification |
| 9 /scaffold | **PASS** | inventaire mis à jour |
| 10 /handoff | **PASS** | 0 placeholder |
| E1–E5 | **PASS** (E1–E4) / N-T (E5 partiel) | refus par règles auto-chargées |
| M1–M5 | **N-T** | à jouer en session interactive |

**verify-e2e.py : 18/18 ✅ (premier run)**

Frictions :
- **F1** — le bug dormant initialement conçu (« remise après TVA ») était **mathématiquement équivalent** au code correct (commutativité) → aucun test ne rougissait, la Phase 6 ne testait rien. Corrigé dans la fixture : remise soustraite en montant absolu. **Leçon de protocole : toujours vérifier que le bug injecté fait ROUGIR avant de dérouler le debug.**

---

## Rapport complémentaire — v0.19.0 : Phase 0 × 5 + Phase B (benchmarks), 2026-07-13

Phase 0 rejouée sur les **5 profils** (harnais scratchpad rsync→render→cleanup→stack-version→
verify-e2e + scans S1/S2/S3 v0.19) puis **Phase B** jouée en agentique sur le jetable
`python-app` (3 scénarios seed).

| Vérification | Résultat |
|---|---|
| Phase 0 × 5 (verify-e2e) | **PASS ×5** (7-8 pass, 0 fail chacun) |
| S1 blocs anti-mauvais-routage post-cleanup | 0 ref morte ×5 (après F6) |
| S2 nav bullets/tables | 0 ref de skill supprimé ×5 |
| S3 contrats v0.19 post-init (Continuation State, DoD, breakers, status) | présents ×5 (selon profil) |
| Phase B `spec/numerotation-continue` | **PASS** (003 = max+1, status: draft, 0 `{{SPEC_*}}`) |
| Phase B `handoff/fresh-regen` | **PASS** (fresh à 19 placeholders, 5 clés Continuation State, journal 1 ligne) |
| Phase B `doc-health/rapport-lecture-seule` | **PASS** (🔴 HANDOFF 10j, 🟠 incohérence status/ROADMAP attrapée, git status inchangé) |

Frictions trouvées puis corrigées (même version) :
- **F6** — les blocs anti-mauvais-routage (v0.19) livraient des **refs mortes sur projets
  générés** : `/scaffold` → bootstrap strippé (tous profils) ; `handoff`/`lecon` → voisins
  strippés (script-jetable). → nouvelle purge `prune_dead_skill_blocks()` dans
  `cleanup-for-type.py` (segments recousus « · », ligne 100 % morte retirée, Réversibilité
  conservée) + bloc 6 de `test_cleanup.py` (67 → 73 checks).
- **F7** — l'Étape 10bis de `/doc-health` (no-op audit) flaggait à tort ses **propres
  exemples** (`/deploy-x`, `/vieux-skill`) et ceux de `/scaffold` → exclusions documentées
  dans le skill (vécu : le grep brut remonte du bruit, scanner en priorité les quote blocks).

### Audit fonction-par-fonction sur jetables (2026-07-13, complément)

59 checks mécaniques/agentiques rejoués sur les jetables `python-app` (état accumulé des
scénarios Phase B) et `brownfield` (neuf) — **0 défaut template** (3 accrocs = bugs des
scripts d'audit eux-mêmes : mkdir manquant, idempotence dédup, sys.path de fixture) :

| Périmètre | Checks | Notes |
|---|---:|---|
| Hooks × 7 (payloads réels post-init) | 20/20 | chmod, snapshots par-session, filet consommé, injection code-map sur src/ + silence .md, growth+dédup, Stop reminder + silence subagent |
| Cycle artefacts `/adr`·`/lecon`·`/idee` | 12/12 | supersede avec **immuabilité vérifiée par hash**, promotion leçon→ADR-0003, idée→spec 004 (max+1), index/CHANGELOG synchro |
| Machine à états spec (003 de bout en bout) | 6/6 | draft→validated→in-progress→done, DoD `command_passes` **réellement exécutée** (unittest vert), ROADMAP↔frontmatter 0 incohérence finale |
| `/codemap`·`/debug`·`/scaffold`·`/pivot` | 12/12 | violation de couplage grep-détectée, debug rouge→vert→leçon, composant conforme (bloc v0.19 + inventaire), chaîne pivot datée |
| Brownfield (adoption projet existant) | 9/9 | fichiers user intacts byte-à-byte (`git status` : 0 modif), aucun strip, blocs non purgés (greenfield only), CORE substitués |

### Déroulé agentique des phases restantes (2026-07-13, même session)

23 checks — phases jamais jouées jusqu'ici, déroulées sur les jetables (0 défaut template) :

| Phase | Checks | Notes |
|---|---:|---|
| 1 — Cadrage + piège bucket (E2) | 3/3 | verbatim client collé tel quel (source datée), ticket → `cadrage/tickets/`, « j'ai eu une idée » → `idees/` (cadrage non pollué) |
| 3 — `/conception` complète (004) | 4/4 | 3 options dont « ne rien faire », décision argumentée, **revue adverse notée** (🔴 resync non atomique → parade `os.replace`), mode TDD gelé dans plan § Décisions |
| 4 — `/feature` pipeline **tdd** (004) | 8/8 | tests AVANT le code, **rouges pour la bonne raison** (NotImplementedError ×8 vérifié), verts sans toucher aux tests (hash identique), parade de revue adverse dans le code livré |
| E — Refus (E1/E3/E4/E5) + M3 | 5/5 | ADR accepted intact par hash + supersede proposé · maillon `/deploy-magique` détecté AVANT exécution · feature-done refusé à 4 tasks non cochées · règle HANDOFF-teammate auto-chargée · deny Read secrets présents |
| 0bis — Rétro-remplissage brownfield | 3/3 | `stack.md` ← pyproject réel, HANDOFF ← `git log` réel + Continuation State, CLAUDE.md mergé (contenu user conservé, exactement 3 @-imports) |

**M4 joué en réel (v1.0.0)** : `claude plugin marketplace add <repo>` + `claude plugin
install agent-teams@claude-setup --scope project` sur jetable → **F8 attrapée** (manifests
invalides au schéma réel : `skills`/`agents`/`hooks` en strings → retirés, auto-découverte)
puis PASS : inventaire complet (1 skill, 4 agents, 3 hooks) + `db-migration` idem.
M1 attesté (découverte auto des skills en session d'audit), M2 couvert (audit hooks payloads réels).

Reste **M5 seul** (interactif pur) — pas-à-pas : sur un jetable initialisé, ouvrir `claude`,
générer du contexte (2-3 gros fichiers lus), `/compact` → vérifier que le snapshot
`.claude/.cache/handoff-snapshot-<session>.md` existe puis que la reprise contient le
marqueur d'injection (hook `SessionStart(compact)`).

⚠️ **Leçon de protocole (vécu)** : `phase0-harness` fait `rmtree` des jetables — ne JAMAIS
re-runner le harnais Phase 0 **après** avoir accumulé de l'état agentique qu'on veut garder
(Phase B et suivantes se jouent APRÈS le dernier run mécanique).

## Rapport complémentaire — Phase 0 × 5 types (mécanique), 2026-07-08

Phase 0 rejouée sur les **5 profils** de `cleanup-for-type.py` via harnais scripté
(rsync documenté → render → cleanup → verify-e2e + scan liens morts/inventaire) :

| Type | verify-e2e | Liens morts | Inventaire mort |
|---|---|---|---|
| script-jetable · automation-n8n · python-app · web-app · bdd-migration | **PASS ×5** | 0 ×5 | 0 ×5 |

Frictions trouvées puis corrigées en v0.18.0 (détail : `.github/CHANGELOG.md`) :
- **F2** — `verify-e2e.py` FAIL sur tout jetable Phase-0-only (HANDOFF jamais exercé compté
  comme raté ; « 3 @-imports » faux pour `script-jetable`) → checks rendus type/état-aware.
- **F3** — `script-jetable` laissait un projet **incohérent** : inventaire avec 11 skills
  morts, section Agent perso vers `agents/` supprimé, 6+ liens de nav morts (conception,
  ADR, stack, cadrage/sous-dossiers) → purges généralisées dans `cleanup-for-type.py`.
- **F4** — le message de fin `automation-n8n` recommandait le plugin **retiré**
  `n8n-expertise` (mort depuis v0.14.0) → plugin officiel `n8n-mcp-skills`.
- **F5** — liens shippés morts dans TOUT projet généré : `../plugins/`, `../EXAMPLES/…`
  (dossiers strippés à l'init) et lien relatif `adr/README.md` cassé depuis `rules/`
  (résolvait `.claude/rules/.claude/docs/…`) → délinkés/corrigés côté template.
