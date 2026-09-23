# Changelog — template claude-Setup

Format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versions [SemVer](https://semver.org/lang/fr/).
Versions du **template lui-même** — distinct du CHANGELOG d'un projet généré (qui vit dans `.claude/docs/CHANGELOG.md`).

## [1.5.0] — 2026-09-23

Revue complète du template (rapport du 2026-09-23) : tout ce qui était vérifiable a été reproduit —
sur des projets générés, sur les 17 versions taguées et en sessions `claude -p` réelles — avant d'être
corrigé. Sur un projet qui a déjà vécu, rien n'était mis à jour : v1.5.0 apporte la mise à jour.

### Added — `/upgrade-template` : les projets générés suivent le template

Jusqu'ici un projet était une copie figée (37 versions en 3 mois ; aucun correctif ne descendait ;
`slim-context.py` avait dû être écrit pour migrer les projets < 1.4 à la main).

- **Moteur `upgrade.py`** (toujours lancé depuis le template le plus récent) : rejoue l'init de la
  version du projet (base) et de la cible — `git archive <tag>` → `render.py` + `cleanup-for-type.py`
  **de cette version**, même profil, variables redéduites des fichiers rendus (jamais stockées : PII) —
  puis fichier de méthode par fichier : projet = base → cible · template inchangé → projet gardé ·
  les deux ont bougé → `git merge-file` (fusion JSON 3 voies pour `settings.json` : règles, hooks
  clés (événement, matcher, commande), clés imbriquées) ; **conflit → fichier du projet gardé**, cible
  + merge annoté dans `.claude/.cache/upgrade-<v>/` + `REPORT.md`. `.claude/docs/` n'est jamais
  fusionné : migrations versionnées idempotentes (< 1.4.0 → `slim-context.py` ; 1.5.0 → note
  multi-agent du gabarit HANDOFF). Arbre git sale refusé, `--dry-run`, `--json`, équipe d'agents
  active préservée.
- **Skill `/upgrade-template`** (manuel) : clone, dry-run montré, validation, application, conflits
  résolus avec l'utilisateur, vérifications, commit. Projets < 1.5 : one-liner dans le README.
- **`.claude/template-lock.json`** écrit à l'init (version, profil, mode, source).
- **Tags rétroactifs** v0.16.0 → v1.4.1 + job CI `tag` : chaque version publiée a sa base de merge.
- `test_upgrade.py` (47 checks) : les 17 versions taguées, non modifiées → **octet pour octet une
  init fraîche** de 1.5.0, code 0, idempotent ; personnalisations gardées ; conflits gardés ;
  projet v1.3.3 « grossi » → journal et gotchas migrés sans perte, budget 31k → 7k tokens.

### Fixed — hooks (vérifié en sessions réelles : `test/live-hooks-check.py`)

- **Filet mémoire : fausse alerte à CHAQUE démarrage.** `SessionEnd` passe toujours après `/handoff`
  → le snapshot était toujours « plus frais » que HANDOFF → « session fermée sans /handoff » injecté
  à chaque session. Désormais le filet n'est écrit que si la session s'est fermée **sans /handoff ET
  en laissant une trace git** (marqueur de début posé par `SessionStart` startup|resume|clear —
  horodatage + empreinte git ; repli : 1re date du transcript). Mesuré avec claude 2.1.280 :
  **v1.4.1 6/10 → v1.5.0 10/10**.
- **Snapshots : les « derniers messages user » étaient vides ou du bruit** (44 entrées `user` sur 45
  sont des `tool_result` ; en fin de session : `caveat / /exit / Goodbye!`). Seuls les messages
  humains sont gardés.
- **Rappel `/handoff` (Stop) une fois par session** — il suivait chaque réponse de Claude.
- **Hook code-map : gotchas ciblés seulement.** Le couplage (déjà en contexte via `code-map.md`
  @-importé, relu après compaction) n'est plus réinjecté ; plus de liste fixe `src/tests/lib/app`
  (ratait `packages/`, `backend/`…) ; gate sur chemin relatif. Doc : l'`additionalContext` d'un
  PreToolUse arrive avec le résultat de l'outil — rattrapage immédiat, pas blocage.
- Purge au démarrage du cache par-session (> 7 jours) ; matchers `Edit|Write` (`MultiEdit` = legacy).

### Fixed — secrets, dérives, contradictions

- **`.gitignore` n'ignorait que `.env` et `.env.local`** : `.env.production/.staging/.development/.test`
  pouvaient partir au commit (`git add .` dans `/feature-done`, `-A` dans `/archive-projet`) → `.env*`
  (hors `.env.example/.sample/.template`) + `secrets.*` ; `git add` sur chemins explicites.
- **gitleaks cité par la rule git-workflow mais absent** → `.pre-commit-config.yaml` (gitleaks
  v8.30.1), activation proposée à l'init.
- `settings.json` : deny secrets à **toute profondeur** avec exceptions `!.env.example` (avant :
  racine seulement) ; `git branch -d/-D` et `git tag -d` demandent confirmation ; allows redondants
  (lecture native) et `autoMemoryEnabled` (défaut) retirés.
- **Gotchas → `code-map-gotchas.md` partout** : `/debug`, `/feature-done` et le protocole d'équipe
  écrivaient encore dans `code-map.md` (auto-chargé) — le bloat corrigé en v1.4.
- **`doc-maintainer` ne fait plus le HANDOFF** (subagent : ni conversation, ni validation possible).
- Rules `code-style`/`testing` : plus d'`AcmeSyncError`/`SapApiError`/`sap_client`, plus de
  « make lint déjà dans pre-commit » inexistant ; **nouvelles rules web** (TS/JS) — le profil
  `web-app` n'avait aucune convention.
- Profil **`other`** (proposé par `/init`, refusé par le script) ; `chmod +x` inutile retiré ;
  liens cassés ; note « 1 HANDOFF par worker » (contredisait la rule d'équipe) ; `/handoff` sans
  branche `main` ; `slim-context` migre toutes les sections Gotchas empilées.

### Changed — budget de contexte au démarrage −41 %

Mesuré par `context-budget.py` sur le template vierge : **11 057 → 6 531 tokens** auto-chargés
(seuil CI 12k → 8k) ; rule `template-maintenance` (chargée à chaque lecture de doc, donc presque
chaque session) : **15 925 → 2 202**.

- `.claude/CLAUDE.md` 7,9 Ko → 2,5 Ko : il ré-inventoriait les skills que Claude Code liste déjà ;
  inventaire canonique (compte CI) → `.claude/skills/README.md`.
- `rules/template-maintenance.md` : 404 → ~70 lignes d'invariants ; formats dans les skills,
  conventions dans `STRUCTURE.md`.
- Listing des skills mesuré comme Claude Code le charge (nom + description, hors
  `disable-model-invocation`) : ~2,2k ; 4 descriptions resserrées ; `/adopt-template` manuel.

### Changed — agent teams réellement opt-in

Le flag `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` n'est pas « inerte sans le plugin » (doc : une équipe
est montée à chaque session, Claude peut proposer des teammates) et la rule d'équipe pesait ~1,8k
tokens sur chaque session de chaque projet. La rule vit dans le plugin ; le 1er `/agent-teams:team`
**active** l'équipe (rule copiée, flag + `teammateMode: "auto"`, relance). Rôles du plugin : « Cadre
de travail » autonome (en mode panes, le corps d'agent **remplace** le system prompt par défaut).
Plugin `agent-teams` 1.1.0.

### Tests

`test_hooks` 62 → 87 (séquences réelles startup → travail → SessionEnd → startup, fixture de
transcript réaliste, purge) · `test_cleanup` 80 → 86 · `test_skills` 148 → 156 ·
`test_context_budget` 33 → 34 · **`test_upgrade`** (nouveau, 47) · **`sim-growth`** (nouveau :
projets qui grossissent session après session) · **`live-hooks-check`** (nouveau, manuel : vraies
sessions `claude -p`) · harnais Phase 0 × 6 profils.

## [1.4.1] — 2026-09-16

### Fixed — le HANDOFF ne peut plus redevenir un journal empilé

Vécu 2026-09-16 sur un projet hors template : `CLAUDE.md` importait 13 docs (780 Ko ≈ 200k tokens),
HANDOFF de **175 Ko** (55 sections datées « préservées » session après session), reprise de session →
`prompt is too long` (1 004 513 > 1 000 000), session bloquée, plafond de dépenses consommé. Claude Code
affiche bien la notice native « Large <fichier> will impact performance (N chars > seuil) » au
démarrage, mais rien n'en découle. Vérifié sur le template v1.4.0 : `CHANGELOG`/`lecons`/`ROADMAP`
sont des liens (jamais importés), 2 `@` seulement ; restait la **règle `/handoff` « préserver les
sections custom »**, exactement le mécanisme d'empilement.

- **`/handoff` Étape 2** : HANDOFF **réécrit** au format strict, jamais appendé ; sections hors format
  conservées seulement si non datées ET fichier < 30 lignes, sinon **déplacées** dans
  `HANDOFF-journal.md` sous `## Archive <date>` (jamais supprimées, dit dans le diff).
- **Hook Stop — garde-fou taille** : HANDOFF > 12 000 octets (~6k tokens) → `systemMessage` avec
  Ko/lignes et le remède, même si le fichier est frais, **une fois par session**
  (`CLAUDE_HANDOFF_MAX_BYTES`, 0 = off).
- **Hook SessionStart(startup) — filet budget** : si `context-budget.py` est présent et que la surface
  auto-chargée dépasse 25k tokens, injecte les 3 coupables + remède (Claude le signale en 1 ligne et
  propose `/doc-health` / `slim-context.py`, sans rien modifier). `CLAUDE_CONTEXT_BUDGET_MAX` (0 = off).
  Silencieux sur `script-jetable` (pas de doc-health).
- Tests : +7 assertions `test_hooks.py` (taille 1×/session, désactivation, budget dépassé/sous seuil/off).

## [1.4.0] — 2026-09-08

### Changed — budget de contexte (« le template lit trop au démarrage »)

Mesuré via `claude -p --output-format json` (usage du 1er tour, Claude Code 2.1.263) : dossier vide
28,7k tokens · template vierge 59,0k · **projet généré d'un mois : 144,0k** (14 % d'un contexte 1M
avant le premier prompt), dont **86,3k pour les 3 `@-imports`** HANDOFF/ROADMAP/code-map (journal
append-only 12,8k est., gotchas 7,2k, « Quand mettre à jour » 4,7k, ROADMAP Phase 1 6,1k) et
**12,1k pour `@rules/template-maintenance.md`** importé depuis `.claude/CLAUDE.md` alors que son
`paths:` le rend déjà conditionnel (vérifié : sans `@`, une rule scopée n'est PAS chargée au
démarrage). Le hook PreToolUse réinjectait en plus ~2,2k tokens à **chaque** Edit/Write, et ces
injections restent dans le transcript pour toute la session (vérifié via `--resume`).
Après migration `slim-context.py` sur le même projet : **59,8k** (−58 %). L'estimation `chars/4` du template sous-évaluait
d'un facteur 2 sur du markdown français → **calibrée à `chars/2`**.

- **`.claude/CLAUDE.md` n'importe plus `@rules/template-maintenance.md`** (lien simple) — la rule
  garde son `paths: .claude/docs/**` et se charge quand on touche la doc. −12k sur tous les projets.
- **HANDOFF : le Journal append-only sort dans `.claude/docs/HANDOFF-journal.md`** (non importé,
  créé par `/handoff` Étape 3bis, migration des entrées existantes sans perte). HANDOFF revient à
  sa règle « < 30 lignes ».
- **code-map scindée** : `code-map.md` (vue macro + couplage + intention, auto-chargée, < 3k tokens)
  / **`code-map-gotchas.md`** (non auto-chargé). Chaque gotcha cite en backticks le chemin/fichier/
  dossier qu'il concerne — c'est la clé de ciblage du hook.
- **Hook `pretooluse-inject-codemap.py` sous budget** : couplage + intention **une fois par
  session** (marker `.claude/.cache/codemap-injected-<session>.json`, effacé par le hook SessionStart
  post-compaction → ré-armé là où le rappel compte) ; gotchas **uniquement ceux qui ciblent le
  fichier édité** (+ § Globaux), une fois par (session, fichier). Fallback sur § Gotchas de
  `code-map.md` pour un projet < 1.4. Tests réécrits (13 assertions).
- **ROADMAP n'est plus importée** (lien simple dans « Lus à la demande ») : dashboard lu
  explicitement par les 11 skills qui en ont besoin. Invariant CI « 3 `@-imports` » → **2**
  (racine + EXAMPLES/acme), `verify-e2e` 1-2, `adopt-template` max 2.
- **Rule `agent-teams.md` réduite aux invariants** (§ Teammate 6 règles, § Lead 5 invariants, ~2,5k
  chars au lieu de 9,5k — auto-chargée partout, teammates compris). Le protocole complet déménage
  dans le plugin : `plugins/agent-teams/skills/team/protocole.md`, lu par `/agent-teams:team`
  (Étape 0). Références mises à jour (plugin README/SKILL/rôles, agents/README, template-maintenance).

### Added

- **`context-budget.py`** (`.claude/skills/doc-health/scripts/`, stdlib) : chiffre la surface
  auto-chargée (index + `@-imports` récursifs ≤ 4 niveaux hors fences/spans + rules non scopées ;
  user et auto-memory à part), flague une rule scopée ré-importée en `@` et les fichiers > 4k tokens
  avec leur remède, `--max` → exit 1. `/doc-health` **Étape 0** (seuil 25k), `/handoff` Étape 5,
  **CI : template vierge < 12k**.
- **`slim-context.py`** (`init-from-template/scripts/`, à lancer depuis le checkout du template
  avec `--root <projet>`) : migration **idempotente** d'un projet < v1.4 — de-`@` des rules scopées,
  journal et gotchas déplacés sans perte, ROADMAP en lien, fichiers v1.4 copiés (hook, rule courte,
  context-budget) avec sauvegarde de l'ancienne rule. `--dry-run` d'abord.
- `test/test_context_budget.py` (32 assertions, en CI) ; placeholder `.claude/docs/code-map-gotchas.md` ;
  `_ON_DEMAND_LINKS` + `HANDOFF-journal.md` (le pointeur survit au cleanup) ; `script-jetable` retire
  aussi `code-map-gotchas.md` ; USAGE § troubleshooting « contexte à 15-20 % au premier prompt » ;
  STRUCTURE : exemple de CLAUDE.md remis en just-in-time (il montrait 12 `@`).

### Migration d'un projet existant

```bash
python3 <template>/.claude/skills/init-from-template/scripts/slim-context.py --root <projet> --dry-run
python3 <template>/.claude/skills/init-from-template/scripts/slim-context.py --root <projet>
python3 .claude/skills/doc-health/scripts/context-budget.py   # dans le projet
```

Hors template (socle ~29k) : `~/.claude/CLAUDE.md` et le hook SessionStart du plugin n8n
(~4k, injecté sur tout projet) pèsent aussi — visibles dans le rapport, hors périmètre ici.

## [1.3.3] — 2026-09-08

### Fixed

- **`cleanup-for-type.py` : les purges post-cleanup respectent le contexte CODE markdown**
  (bug vécu sur un projet généré 2026-09-08, reproduit sur les 5 profils) — dans
  `.claude/rules/template-maintenance.md`, 3 blocs légitimes étaient perdus à chaque init :
  `` `![](path)` `` (syntaxe citée en code inline → « lien mort »), `[path/to/spec](path)`
  du pattern HANDOFF fencé (idem) et `## Contexte / ## Options considérées / ## Décision` du
  pattern ADR fencé (repliés comme « sections vides »). Nouveau masque `_fenced()` (blocs
  ``` / ~~~) + `_in_code_span()` partagés par `prune_dead_nav_links`, `_drop_empty_sections`,
  `_drop_section` et `prune_dead_inventory` : **un bloc fencé est un exemple, jamais de la
  navigation, de la structure ni de l'inventaire — aucune purge n'y touche** (y compris une
  réf `` `/skill` `` mort citée dans un exemple). Garde-fou 7 + 4 assertions dans
  `test/test_cleanup.py` (rouges sur l'ancien script).

## [1.3.2] — 2026-09-02

### Changed

- **Hook growth-detection : guard élargi à tout `.claude/`** (au lieu de `.claude/docs/` +
  `.growth-suggestions.md`) — pattern battle-testé sur un projet généré (fix indépendant
  2026-06-10, après 3 purges de faux positifs) : les rules/skills/hooks parlent légitimement
  de « credentials »/« deploy »/« prod » sans être du code projet. Test de régression ajouté.
- **Hook stop-handoff-reminder : silencieux sur un projet archivé** (marqueur
  `.claude/archived` de `/archive-projet` présent) — un projet en lecture seule n'a pas à
  rappeler `/handoff`. Test ajouté.
- **PROTOCOL-E2E § Phase B : ordre des benchmarks** — jouer `archive-projet/*` en DERNIER
  (s'il va jusqu'au move réel, le jetable change de chemin), ou s'arrêter au `--dry-run`.

## [1.3.1] — 2026-09-02

### Changed

- **`Read(./.claude/docs/ACCESS.md)` retiré du `deny` de `settings.json`** (demande Julien) :
  ACCESS.md documente **où** vivent les accès (nom de variable, fichier, URL de console), pas
  les valeurs — le deny empêchait Claude de s'en servir pour ce à quoi il sert (retrouver un
  accès, enrichir via growth-detection). Les vraies protections restent : `.env*` / `secrets.*`
  en deny, et la règle « jamais de valeur en clair dans ACCESS.md » (USAGE § permissions).

## [1.3.0] — 2026-08-31

### Added

- **Skill `/archive-projet`** (16ᵉ skill cœur) — fin de vie d'un projet, sans angle mort :
  bilan de fermeture (HANDOFF final, ROADMAP gelée à l'état réel, entrée CHANGELOG, leçon
  post-mortem optionnelle), marquage archivé visible par toute session future (bannière en
  tête du CLAUDE.md racine entre marqueurs HTML + marqueur machine-lisible `.claude/archived`
  avec chemins aller/retour), scan des références au chemin absolu (repo + crontab +
  `~/.claude.json`, rapport seul), migration de l'auto-memory (`~/.claude/projects/<slug>`),
  et **commande finale remise à l'utilisateur** (`mkdir` + `mv` projet + `mv` mémoire) à
  lancer après fermeture de la session — le script ne déplace jamais le dossier dans lequel
  la session tourne. Pré-flights bloquants : déjà archivé, worktrees actifs, destination
  occupée. Sous-modes `restore` (dé-archivage symétrique) et `status`. Slash-only
  (`disable-model-invocation: true`). Destination **choisie par l'utilisateur au moment de
  l'archivage** (AskUserQuestion — défaut proposé `<parent>/_archives/<projet>`, tout autre
  dossier via `--dest`).
  Mécanique déterministe dans `scripts/archive-projet.py` (stdlib, `--dry-run` partout),
  couverte par la nouvelle suite `test/test_archive.py` (34 checks, branchée en CI) + un
  scénario benchmark Phase B. Survit à tous les profils de cleanup (aucun type ne le retire).

### Fixed

- **Hook growth-detection : boucle auto-référentielle au tri des suggestions** (vécu
  2026-09-02 sur un projet généré, fixé là-bas en `43ce101` puis backporté ici) : en triant
  `.claude/.growth-suggestions.md`, le hook PostToolUse scannait le tri lui-même, retrouvait
  « credentials »/« prod » dans les lignes barrées et **regénérait des suggestions dans le
  fichier en cours de nettoyage**. Le hook s'ignore désormais lui-même
  (`file_path.endswith(".growth-suggestions.md")` → skip) + test de régression dans
  `test_hooks.py`. Projets déjà générés : reporter la ligne à la main (1 ligne).

## [1.2.4] — 2026-08-31

### Changed

- **Plugin n8n : check-first au lieu d'une install proposée systématiquement.** L'étape « plugin
  stack » de `/init-from-template`, le pipeline `n8n` et la doc proposaient à chaque projet
  `/plugin marketplace add czlonkowski/n8n-skills` + install `--scope project` — soit un re-clone
  du repo à chaque init, alors que le plugin est généralement déjà installé en **user-scope**
  (une install couvre tous les projets). Nouvelle doctrine partout : **vérifier d'abord**
  (`claude plugin list`) → déjà en scope `user` = confirmation en UNE ligne, rien à cloner ;
  absent = proposer l'install **`--scope user`** (une fois pour toutes). Touchés : SKILL
  `/init-from-template`, `cleanup-for-type.py` (message keep_reason), `.claude/CLAUDE.md`,
  `USAGE.md`, `skills/README.md`, `rules/template-maintenance.md`, pipeline `n8n`,
  quick-start `.github/README.md`, exemple ACME. `db-migration` reste par projet
  (marketplace `claude-setup`).

## [1.2.3] — 2026-08-04

### Fixed

- **Hooks cassés si le chemin du projet contient un espace** (trouvé à l'init d'un projet réel) :
  les commandes de hooks ne quotaient pas `${CLAUDE_PROJECT_DIR}` (7 occurrences dans le
  `settings.json` shippé) ni `${CLAUDE_PLUGIN_ROOT}` (3 occurrences dans le `hooks.json` du
  plugin `agent-teams`) → le shell coupait le chemin au premier espace et aucun hook ne se
  déclenchait. Variables désormais quotées (`\"${CLAUDE_PROJECT_DIR}\"`) + note quoting dans
  USAGE.md § troubleshooting hooks. Projets déjà générés : ajouter les quotes dans
  `.claude/settings.json` à la main.

## [1.2.2] — 2026-08-03

### Added

- **Agent teams — garde-fous anti-« teammate figé au spawn »** (vécu sur projet généré) : un
  `cd` Bash du lead **persiste** et est **hérité** par les teammates → spawnés depuis un
  sous-dossier, ils démarrent leur session là-bas et se figent EN SILENCE sur le dialogue
  « Allow external CLAUDE.md file imports? » (approbation keyée par chemin dans
  `~/.claude.json` : celle de la racine ne couvre pas le sous-dossier) — indistinguables
  d'agents morts (pas d'erreur, pas d'idle ping, SendMessage non lus → respawns en double).
  Encodé dans `rules/agent-teams.md` § Lead : sous-section **Spawn** (toujours depuis la
  racine, `cd "$(git rev-parse --show-toplevel)"`) + § Suivi (**teammate silencieux ≠ mort** :
  `tmux capture-pane -p -t <pane>` avant respawn ; déblocage `tmux -L <socket> send-keys -t
  <pane> Enter`, socket via `ls /tmp/tmux-$UID/`). Relayé dans `/agent-teams:team` (Étapes 4-5
  + anti-patterns) et `/init-from-template` Étape 0 (l'approbation d'imports est
  machine-locale, non shippable).

## [1.2.1] — 2026-07-13

### Fixed

- **Règles `Write(path)` mortes dans le `settings.json` shippé** : depuis Claude Code ~2.1.x,
  seules les règles `Edit(path)` sont matchées par les checks de permission fichier (et elles
  couvrent TOUS les outils d'édition — Write, Edit, NotebookEdit) → chaque session d'un projet
  généré affichait des warnings de dépréciation. Les 3 règles `Write(./.claude/docs/**)`,
  `Write(./src/**)`, `Write(./tests/**)` étaient de plus **redondantes** (le `Edit(./**)`
  global les couvrait déjà) → supprimées. Projets déjà générés : retirer les lignes `Write(`
  de `.claude/settings.json` (une commande, voir ci-dessous).

## [1.2.0] — 2026-07-13

### Changed

- **P2 — `specs/` promu au rang de bucket frère** : `.claude/docs/conception/specs/` →
  `.claude/docs/specs/` (specs à 4 niveaux au lieu de 5). **`conception/` reste intact**
  (les 5 md du « PRD from scratch » + diagrams/) — seul le bac à features remonte. Le
  pattern mirror macro↔micro est inchangé (il est conceptuel). 27 fichiers ré-alignés
  (skills, templates ROADMAP/HANDOFF, rules, STRUCTURE arbre redessiné, EXAMPLES/acme
  déplacé, verify-e2e, harnais, benchmarks) ; `script-jetable` strippe le nouveau chemin.

### Added

- **P5 — mode macro express** (`/conception macro`) : par défaut si le MVP tient en ≤ 3 specs —
  PRD 1 page (≤ 5 features, Scope OUT obligatoire), ARCHITECTURE ~10 lignes + ASCII, tasks =
  table de découpage seule. Le design profond part dans le micro de la feature 1 : on ne
  conçoit plus deux fois avant la première ligne de code.
- **P6 — règle « spec 001 = tranche verticale »** (encodée dans `/conception` macro + le
  template `conception/tasks.md` § 1.1) : la première spec traverse le système de bout en
  bout, même moche — dé-risque l'archi tôt ; le transverse devient sa propre spec.

### Rejected

- **P4 — index `README.md` à la racine de `docs/`** : testé avec/sans sur jetable — 8 READMEs
  de bucket existent déjà + CLAUDE.md (nav, auto-chargé) + rule template-maintenance (matrice,
  auto-chargée en écrivant dans docs/). 0 % d'info nouvelle = 3ᵉ copie à drift garanti.

## [1.1.0] — 2026-07-13

Revue d'arbo « yeux frais » sur 3 jetables : la racine d'un projet généré passe de 8 entrées
(dont **1 631 lignes de doc de MÉTHODE** — les 2 plus gros fichiers que voyait le client)
à **5 entrées** : seuls `CLAUDE.md` et `README.md` restent visibles.

### Changed

- **P1 — `USAGE.md` + `STRUCTURE.md` déplacés à la racine → `.claude/`** : la règle du
  template (« info projet → racine ; info template/outillage → `.claude/` ») s'applique
  enfin à sa propre doc. Liens internes ré-ancrés (`](.claude/…` → `](…`, `EXAMPLES` →
  `../EXAMPLES`), toutes les réfs alignées (README, `.claude/CLAUDE.md`, rules, CI,
  cleanup NAV, harnais, test_cleanup). **`script-jetable` les STRIPPE entièrement**
  (1 600 lignes de méthode pour un 1-shot = overkill assumé du profil -80 %).

### Fixed

- **P3 — `vars.json` d'init (PII : emails, noms)** : le harnais l'écrivait dans le projet
  et l'y laissait → écrit HORS projet (comme le skill) + **filet dans `cleanup-for-type`**
  (supprime un `vars.json` racine oublié s'il contient nos clés CORE, greenfield only).
  `test_cleanup` : 73 → 76 checks (strip USAGE/STRUCTURE jetable, conservation python-app,
  filet vars).

## [1.0.0] — 2026-07-13

**Première version production.** Critères de promotion : protocole E2E intégralement joué
(Phase 0 ×5, 0bis, 1-10, B, E, M1-M4 — M5 reste interactif pur), 262 checks CI mécaniques,
~90 vérifications sur 7 projets jetables, 0 défaut résiduel — chaque friction trouvée
(F6-F8) est corrigée ET verrouillée par un test.

### Added

- **`test/phase0-harness.py` versionné + branché en CI** : l'outil qui a attrapé F6 (init
  réelle rsync→render→cleanup→verify-e2e + scans S1/S2/S3 sur les 5 profils) tourne
  maintenant à chaque push — plus un script de session perdu comme le harnais v0.18.
  **Garde-fou anti-`rmtree` encodé** (leçon v0.19) : refuse d'écraser un jetable contenant
  de l'état agentique sans `--force`.

### Fixed

- **F8 — plugins ininstallables (attrapé par M4 réel, `claude plugin install`)** : les
  `plugin.json` déclaraient `skills`/`agents`/`hooks` en strings, invalides au schéma réel
  (`Validation errors: agents: Invalid input`) — la CI vérifiait la cohérence des manifests,
  jamais leur installabilité. Fix : champs retirés, **auto-découverte du layout standard**.
  Vérifié : `agent-teams@claude-setup` (1 skill + 4 agents + 3 hooks inventoriés) et
  `db-migration@claude-setup` s'installent en `--scope project`.

### Verified

- **M4 joué en réel** : `claude plugin marketplace add` + install des 2 plugins maison sur
  jetable, inventaire de composants complet. **M5** (compaction réelle) : pas-à-pas documenté
  dans PROTOCOL-E2E — seul résidu interactif pur.

## [0.19.0] — 2026-07-13

Moisson [Citadel](https://github.com/SethGammon/Citadel) (SethGammon, MIT) : après comparaison
approfondie des deux systèmes, adoption de 4 idées compatibles avec notre philosophie
(markdown pur, zéro runtime) — testabilité des skills, critères de fin vérifiables,
état machine-readable, anti-mauvais-routage. Détail de l'analyse : leur `Decision Log` meurt
avec la campagne archivée là où nos ADR survivent ; en échange, leur culture « une instruction
se teste comme du code » nous manquait — c'est corrigé ici.

### Added

- **`test/test_skills.py`** (4ᵉ suite CI, stdlib) : un SKILL.md est du code d'instruction —
  frontmatter (`name` = dossier, description), bloc anti-mauvais-routage présent avec voisins
  **existants** (même résolution que le check pipelines : cœur + `plugin:skill` + externes +
  builtins), réversibilité typée, contrats v0.19 des templates bundlés (DoD typée, circuit
  breakers, `status:`, Continuation State), structure des scénarios benchmarks. 132 checks.
- **`test/benchmarks/`** (pattern `__benchmarks__/` de Citadel) : scénarios comportementaux
  par skill (frontmatter `input`/`state`/`assert-contains`) — structure validée en CI,
  exécution agentique via **PROTOCOL-E2E Phase B** (nouvelle). 3 seeds : `handoff/fresh-regen`,
  `doc-health/rapport-lecture-seule`, `spec/numerotation-continue`.
- **Bloc anti-mauvais-routage dans les 15 skills cœur** : « **Quand ne PAS utiliser** » nommant
  1-2 skills voisins (le bon routage vient des voisins nommés, pas de la description) +
  « **Réversibilité** » typée 🟢/🟠/🔴 avec undo littéral. Convention encodée dans `/scaffold`
  (mode skill, étape 3) et exigée par `test_skills.py`.
- **DoD typée dans `spec/templates/tasks.md`** : `command_passes:` / `file_exists:` / `manual:`
  — le critère de fin devient exécutable, pas interprétable. + budget **~35 min de travail
  agent par phase** (au-delà, l'agent « perd le fil » — télémétrie Morph 2026 via Citadel).
- **§ Circuit breakers dans `spec/templates/plan.md`** : conditions d'arrêt décidées À FROID
  à la conception (3 échecs consécutifs → replanifier, etc.) — `/conception` Étape 4 les remplit.
- **Frontmatter `status:` machine-readable sur `spec.md`** (draft/validated/in-progress/done/
  parked) : posé par `/spec`, `validated` par `/conception` Étape 6, `done` par `/feature-done`
  Étape 3 ; **cohérence ROADMAP ↔ frontmatter auditée par `/doc-health`** (Étape 8 étendue).
- **Continuation State dans HANDOFF** (template + `/handoff` + pattern minimal de
  template-maintenance) : 5 clés `Clé: valeur` fixes (Spec/Task/Fichiers en cours/Bloqué sur/
  Commande de reprise) — le point de reprise parseable quand la prose ambiguë coûte cher.
- **`/doc-health` Étape 10bis — no-op audit des instructions** (inspiré du no-op detector
  Citadel) : références `/skill` mortes, chemins morts (whitelist création-différée),
  placeholders résiduels dans les skills maison — en CI pour le template (`test_skills.py`),
  agentique pour les projets générés.

### Fixed

- **F6 — refs mortes livrées par les blocs anti-mauvais-routage sur projets générés**
  (attrapé par la Phase 0 × 5 rejouée) : `/scaffold` routait vers les bootstrap strippés
  (tous profils) ; `handoff`/`lecon` vers des voisins strippés (script-jetable). → nouvelle
  purge **`prune_dead_skill_blocks()`** dans `cleanup-for-type.py` : segments morts retirés
  et recousus (« · »), ligne « Quand ne PAS utiliser » 100 % morte retirée entière (la
  « Réversibilité » reste), logique positive (jamais les builtins/plugins namespacés).
  `test_cleanup.py` bloc 6 (67 → 73 checks).
- **F7 — auto-faux-positifs du no-op audit** : l'Étape 10bis de `/doc-health` flaggait ses
  propres exemples (`/deploy-x`, `/vieux-skill`) et ceux de `/scaffold` → exclusions
  documentées + priorité de scan aux quote blocks et skills ajoutés par le projet.
- Ajouts `template-maintenance.md` reformatés en **bullets purgeables** (la purge
  d'inventaire opère par bullet/rangée — une prose flèche `→` y échappait sur script-jetable).

### Vérifié sur projets générés (2026-07-13)

- **Phase 0 × 5 profils** (harnais rsync→render→cleanup→verify-e2e + scans blocs/nav/contrats) :
  **PASS ×5**, 0 ref morte post-purge, contrats v0.19 présents.
- **Phase B (agentique, jetable python-app)** : `spec/numerotation-continue` PASS (003 = max+1,
  `status: draft`, 0 `{{SPEC_*}}`) · `handoff/fresh-regen` PASS (fresh à 19 placeholders,
  5 clés, journal 1 ligne) · `doc-health/rapport-lecture-seule` PASS (🔴 10j + 🟠 incohérence
  attrapées, git status inchangé). Détail : `test/PROTOCOL-E2E.md` § Rapport v0.19.0.
- **Audit fonction-par-fonction sur jetables (59 checks, 0 défaut)** : hooks × 7 avec payloads
  réels (20/20), cycle `/adr`·`/lecon`·`/idee` avec immuabilité vérifiée par hash (12/12),
  machine à états spec de bout en bout avec DoD exécutée pour de vrai (6/6),
  `/codemap`·`/debug`·`/scaffold`·`/pivot` (12/12), **brownfield** : adoption sur projet
  existant, 0 fichier user modifié (9/9). Table complète : PROTOCOL-E2E § Audit.
- **Déroulé agentique des phases restantes (23 checks, 0 défaut)** : Phase 1 cadrage + piège
  bucket, Phase 3 conception complète (options + revue adverse appliquée jusqu'au code),
  Phase 4 pipeline **TDD** (rouges pour la bonne raison → verts, tests intouchés par hash),
  Phase E refus E1/E3/E4/E5, Phase 0bis rétro-remplissage. Le protocole E2E est intégralement
  joué hors M4/M5 (interactifs purs). Table : PROTOCOL-E2E § Déroulé agentique.

### Notes

- Idées Citadel **écartées** (incompatibles avec la philosophie du template) : runtime JS +
  router 4-tiers (49 skills → nécessaire ; 15 bien nommés → non), télémétrie/dashboard
  (absorbés par les vendors — leur propre lab report le documente), trust levels (produit
  multi-utilisateurs, pas solo-dev).

## [0.18.0] — 2026-07-08

Phase 0 du protocole E2E rejouée mécaniquement sur les **5 types** de `cleanup-for-type.py`
(harnais rsync→render→cleanup→verify-e2e + scan liens/inventaire) : 4 frictions corrigées
(F2-F5, détail dans `test/PROTOCOL-E2E.md` § Rapport complémentaire). Résultat : **PASS ×5,
0 lien mort, 0 inventaire mort** sur les cinq profils.

### Added

- **Cohérence post-cleanup par profil** (`cleanup-for-type.py`) : la purge d'inventaire est
  généralisée des seuls skills bootstrap à **tous les skills supprimés par le profil** —
  bullets et rangées de table dans `.claude/CLAUDE.md`, `rules/template-maintenance.md`,
  `USAGE.md` et `CLAUDE.md` racine (forme d'invocation backtickée `` `/nom `` uniquement,
  jamais les chemins), compte « **N skills cœur** » recalé, sous-sections vidées repliées,
  sections structurellement mortes retirées (« Agent perso »/« Agents disponibles » si
  `agents/` part, « Pipelines récurrents » si `/feature` part, « Agent teams » si la rule
  part). Nouvelle purge des **liens de navigation morts** (CLAUDE.md racine,
  `cadrage/README.md`, `template-maintenance.md`) avec recouture des séparateurs « · » —
  les pointeurs create-on-demand (ACCESS/GLOSSARY/RUNBOOK/STAKEHOLDERS) et les
  liens-patterns sont **conservés**. Greenfield uniquement (jamais en `--brownfield`).
- `script-jetable` supprime aussi `.claude/rules/agent-teams.md` — protocole d'équipe
  auto-chargé à chaque session, sans objet sur un 1-shot (agents déjà retirés).
- `test/test_cleanup.py` : bloc 5 « cohérence script-jetable » + assertions non-régression
  python-app/dry-run (40 → 67 checks).

### Fixed

- **`cleanup-for-type.py` (type `automation-n8n`)** : le message de fin recommandait encore
  le plugin **retiré** `n8n-expertise` (`/plugin install n8n-expertise@claude-setup`,
  mort depuis v0.14.0) → plugin officiel `n8n-mcp-skills` (czlonkowski/n8n-skills).
- **`verify-e2e.py`** ne FAIL plus sur un jetable qui n'a joué que la Phase 0 : HANDOFF
  jamais exercé (template intact) → **skip** au lieu de fail ; « 3 @-imports » strict →
  « 1-3 @-imports, tous vivants » (`script-jetable` en garde légitimement 1 après purge).
- **Liens shippés morts dans tout projet généré** : réfs `../plugins/` et `../EXAMPLES/…`
  délinkées dans `.claude/CLAUDE.md` + `conception/specs/README.md` (dossiers strippés à
  l'init) ; lien `adr/README.md` de `rules/template-maintenance.md` **cassé partout**
  (relatif depuis `rules/` → résolvait `.claude/rules/.claude/docs/…`) corrigé en
  `../docs/adr/README.md`.
- `init-from-template/SKILL.md` Étape 4 : la traçabilité `stack.md` est sautée en
  `script-jetable` (le profil supprime le fichier — la trace = `.claude/template-version`).

## [0.17.0] — 2026-07-07

### Added

- **Protocole E2E agentique** (`test/PROTOCOL-E2E.md`) — le trou de couverture restant : les suites mécaniques gardent scripts/hooks/manifests, RIEN ne testait qu'une session Claude suivant les skills produit les bons artefacts. Protocole rejouable à chaque version majeure : fixture « caisse » (mini-app réelle + bug dormant), **12 phases** (greenfield, brownfield, cadrage+piège bucket, spec, conception, pipeline tdd, artefacts+supersede, debug, feature-done+pivot, doc-health+codemap, scaffold, handoff), **cas d'erreur E1-E5** (tester les REFUS : ADR immuable, buckets, maillon absent…), **phases M** manuel-assisté (auto-invocation, hooks réels, permissions, plugins, compaction — honnêtement classées non-testables headless), verdicts PASS/PARTIEL/FAIL/N-T + F-notes (successeur méthodologique de TEST-REPORT F1→F10).
- **`test/verify-e2e.py`** — vérificateur scripté des invariants post-run (stdlib, tolérant à la matière absente) : CORE=0, bootstrap purgé, 4 fichiers/spec, numérotation continue, specs↔ROADMAP, statuts ADR + cohérence `supersedes`, leçons statutées, HANDOFF sans placeholder, version tracée dans stack.md.

### Notes — étalonnage réel (fixture « caisse »)

- 12 phases + E1-E4 jouées : **PASS** ; `verify-e2e.py` : **18/18 au premier run**.
- **F1 attrapée par l'étalonnage** : le bug dormant conçu pour la Phase 6 (« remise après TVA ») était mathématiquement équivalent au code correct (commutativité) → aucun rouge, le debug ne testait rien. Fixture corrigée (remise en montant absolu), phase rejouée avec rouge observé. Un protocole jamais joué ment.

## [0.16.0] — 2026-07-07

Durcissement final post-revue de système : gardes permanentes, fin des comptes dupliqués, traçabilité de version, régime de contexte.

### Added

- **CI « pipelines → maillons existants »** : chaque `/x` référencé dans `feature/pipelines/*.md` doit résoudre (skill cœur, plugin maison, namespace officiel connu, built-in) — le check fait 2× à la main pendant la revue est maintenant permanent.
- **CI « compte auto-vérifié »** : le nombre déclaré dans « **N skills cœur** » (`.claude/CLAUDE.md`) doit égaler le nombre réel de dossiers — le compte ne peut plus mentir.
- **Traçabilité de version** : nouveau fichier **`.claude/template-version`** (copié dans chaque projet généré et conservé) + check CI « version = tête du CHANGELOG » ; `/init-from-template` et `/adopt-template` notent `Template claude-Setup vX.Y.Z` dans `stack.md` → base d'un futur `/template-update`.

### Changed

- **Fin des comptes dupliqués** (2 erreurs de synchro aujourd'hui) : le nombre de skills ne vit QUE dans `.claude/CLAUDE.md` (CI-vérifié) ; README, USAGE (table des types), STRUCTURE dé-numérotés (pointeurs vers l'inventaire canonique).
- **Régime de contexte des rules** (mesuré : **~12,2k tokens** auto-chargés/session — 8× la philosophie « ~1,5k » du CLAUDE.md) : `template-maintenance.md` **scopée `paths: .claude/docs/**`** (chargée quand on écrit de la doc — son déclencheur déclaré) **+ dégraissée** (tables « Skills/Agents EN PLACE » supprimées : dupliquaient l'inventaire `.claude/CLAUDE.md` et `agents/README` — et avaient déjà drifté). `code-style`/`testing` étaient déjà scopées `**/*.py`. Reste auto-chargé en permanence : agent-teams + doc-lookup + git-workflow ≈ **2,9k tokens** (−76 %).
- **Hygiène de version des plugins maison** : rappel mainteneur dans les README de `db-migration`/`agent-teams` + dans `/scaffold` (bump `plugin.json` à chaque modif, sinon `/plugin marketplace update` ne propage rien de visible).

## [0.15.0] — 2026-07-07

### Added

- **Skill `/scaffold skill|agent|pipeline "<nom>"`** (15e skill cœur) — **générateur de composants conformes** : les conventions gardées par la CI sont encodées à la création au lieu d'être rattrapées après. Mode **skill** (name = dossier, description auto-invocante, `disable-model-invocation` pour le sensible, + ligne d'inventaire `.claude/CLAUDE.md`). Mode **agent** (teammate → `SendMessage` obligatoire, libs externes → `mcp__context7`, + ligne `agents/README`). Mode **pipeline** en 2 façons : **dirigé** (l'utilisateur dicte l'ordre des étapes + maillons/MCP de chacune — le skill vérifie l'existence de chaque maillon et complète les critères de sortie) ou **proposé** (l'utilisateur décrit la tâche récurrente — le skill inventorie les maillons disponibles, instancie la grammaire Planifier→…→Persister et propose le pipeline optimal, l'utilisateur tranche). Étape 0 anti-doublon systématique + rappels contextuels (repo template : comptes/CHANGELOG ; projet généré : rien de plus). `script-jetable` le retire.

## [0.14.0] — 2026-07-07

### Changed

- **Stack n8n : plugin vendored → plugin OFFICIEL upstream.** Les 7 skills du plugin `n8n-expertise` provenaient du projet [n8n-mcp](https://github.com/czlonkowski/n8n-mcp) (MIT) — et czlonkowski les distribue **lui-même** comme plugin Claude Code via le repo dédié [`n8n-skills`](https://github.com/czlonkowski/n8n-skills) : marketplace `n8n-mcp-skills`, **14 skills** (nos 7 + error-handling, subworkflows, agents, binary-and-data, code-tool, multi-instance, self-hosting + skill routeur) **+ hooks d'enforcement**, v1.23.0, activement maintenu. Notre copie (sous-ensemble driftant, auteur mal attribué) est **supprimée** ; le template référence l'officiel : `/plugin marketplace add czlonkowski/n8n-skills` puis `/plugin install n8n-mcp-skills@n8n-mcp-skills`. Le marketplace `claude-setup` ne garde que les plugins **maison** (`db-migration`, `agent-teams`). Pipeline `n8n` re-namespacé `/n8n-mcp-skills:*` (+ appui `n8n-error-handling` à l'étape Tester).

## [0.13.0] — 2026-07-07

### Added

- **Pipeline `n8n`** (3e fichier de `feature/pipelines/`) — implémentation d'un workflow d'automatisation : Planifier (pattern choisi via `n8n-workflow-patterns`) → Construire (outils n8n-mcp + skills du plugin `n8n-expertise` : node-configuration, expression-syntax, code-js/py) → **Valider** (validation n8n-mcp + `n8n-validation-expert`, faux positifs écartés) → **Tester en réel** (cas nominal ET cas d'erreur, sortie de chaque nœud inspectée) → Review adverse sur l'**export JSON** (secrets absents, idempotence, rate limits) → Persister (**JSON versionné dans `workflows/`** + RUNBOOK si prod). Illustre la doctrine : le squelette (Planifier→…→Persister) est universel, chaque contexte instancie ses étapes — nouveau fichier pipeline seulement quand une étape change de **nature**, pas d'outil.

## [0.12.1] — 2026-07-07

### Fixed

- **Grep de vérification post-init trop large** (découvert par test E2E sur projet jetable) : il matchait les `{{SPEC_*}}` des templates bundlés de `/spec` (qui DOIVENT garder leurs placeholders — c'est le scaffold) → faux « ❌ CORE restants ». Périmètre restreint aux fichiers réellement substitués (`CLAUDE.md`, `README.md`, `.env.example`, `.claude/CLAUDE.md`, `.claude/docs/`, `.claude/rules/`).

### Notes — E2E validé sur 2 projets jetables

- **python-app** : rsync → chmod → git init → render (20 substitutions, 0 CORE) → cleanup (strip complet, 2 allow-rules + 10 lignes d'inventaire purgées) → hooks smoke-testés → **pipeline `tdd` déroulé en entier** (spec scaffoldée depuis les templates, auto-sélection TDD via plan.md § Décisions, tests ROUGES → code VERT, review adverse, DoD, ROADMAP/CHANGELOG/HANDOFF).
- **script-jetable** : -80% → il reste exactement `handoff`+`lecon`, hooks fantômes et @-imports cassés auto-réparés, settings valide.

## [0.12.0] — 2026-07-07

### Added

- **Skill `/feature "<titre>" [pipeline]`** (14e skill cœur) — **orchestrateur de pipeline** : déroule une feature de bout en bout en enchaînant les maillons EXISTANTS (`/spec` → `/conception` → solo|`/agent-teams:team` → tests → `reviewer` adverse → vérif DoD → `/feature-done`), avec **gate utilisateur entre chaque étape** et reprise propre après un stop. **1 pipeline = 1 fichier déposable** dans `feature/pipelines/` — extensible au fil de l'eau sans toucher l'orchestrateur. Livrés : `standard` (Planifier → Coder → Tester → Review → Vérifier → Persister) et `tdd` (Planifier → **Écrire les tests rouges** → Coder vert → Review → Vérifier → Persister). Auto-sélection : `/conception` note le mode par spec dans `plan.md § Décisions` → `/feature` le respecte.
- **Section « 🔁 Pipelines récurrents » dans `.claude/CLAUDE.md`** (auto-chargé) : les 3 séquences canoniques (standard, tdd, bug) visibles d'un coup d'œil — fini le « je ne me les rappelle plus ».

### Changed

- Comptes et inventaires synchronisés (**14 skills cœur**) ; `script-jetable` retire aussi `/feature` (overkill pour un 1-shot).

## [0.11.0] — 2026-07-07

Étape 2 du plan plugins : l'**exécution d'équipe** sort du cœur — un projet solo/n8n n'embarque plus les rôles web.

### Added

- **Plugin `agent-teams`** (3e plugin du marketplace) : skill **`/agent-teams:team`** (orchestration tmux — plan validé, worktrees, task list native, TDD opt-in, merge, débrief mémoire) + **rôles d'exécution** `worker`/`front-end`/`back-end`/`tester` + **hook de trace** `teamtask-log` (TaskCreated/TaskCompleted/TeammateIdle via `hooks.json` du plugin). Install : `claude plugin install agent-teams@claude-setup --scope project`.
- Matrice « quand créer un fichier » : trigger **STAKEHOLDERS.md** (> 4-5 interlocuteurs → modèle prêt dans STRUCTURE.md § STAKEHOLDERS) — clôt **F9**, le dernier item du backlog TEST-REPORT.

### Changed

- **Restent dans le cœur** (dépendances des skills cœur) : `reviewer` (revue adverse `/conception` + diffs d'équipe), les 3 explorateurs, la rule `agent-teams.md` (protocole, SOURCE UNIQUE) et le câblage `settings.json` (flag agent-teams + `teammateMode` — inertes sans le plugin). **13 skills cœur** (comptes et inventaires synchronisés : `.claude/CLAUDE.md`, README repo, USAGE, STRUCTURE, template-maintenance, agents/README).
- `settings.json` : hooks TaskCreated/TaskCompleted/TeammateIdle retirés (livrés par le plugin) ; `test_hooks.py` teste le hook à son emplacement plugin ; CI : la garde SendMessage couvre aussi `plugins/*/agents/*.md`.

### Removed

- **`test/build-plugin.py`** (proto « tout-`.claude/`-en-un-plugin ») — supplanté par le vrai marketplace `claude-setup` : les composants distribuables sont désormais des plugins dédiés (`plugins/`), le cœur reste un scaffold copié par rsync+init (rules, docs et settings ne sont pas transportables en plugin).

## [0.10.0] — 2026-07-07

### Added

- **Rule `doc-lookup.md`** (SOURCE UNIQUE, auto-chargée) : politique de recherche de doc externe pour toute session, skill et agent — **jamais de réponse de mémoire** pour une API/version ; ordre **context7 (MCP)** → autres MCP docs → WebFetch/WebSearch ; toute affirmation sourcée (version + URL) ; recherche large → `explore-docs`. context7 supposé connecté **user-level** (fallback web sinon).

### Changed

- **Câblage de la politique là où elle manquait** : `/debug` étape 2 spawn aussi `explore-docs` quand une lib/API externe est en jeu (+ `mcp__context7` dans ses allowed-tools) ; `mcp__context7` ajouté aux **5 rôles teammate** (`worker`, `front-end`, `back-end`, `tester`, `reviewer`) — doc versionnée en direct sans ouvrir le web aux codeurs ; pointeurs vers la rule dans `explore-docs`, le plugin `db-migration` (doc Alembic à jour), le `CLAUDE.md` racine (liens conventions), `STRUCTURE.md` (arbre rules/) ; prérequis « MCP context7 user-level » documenté dans USAGE. (`/conception` + `explore-docs` étaient déjà câblés.)

## [0.9.1] — 2026-07-07

Post-review complète (workflow multi-agents : 15 findings confirmés + vérifs inline + sweep) — durcissement init/adopt et correctifs de cohérence.

### Fixed

- **🔴 `/adopt-template` détruisait les dossiers du PROJET** : `strip_template_maintenance` supprimait sans condition `.github/`, `test/`, `plugins/` — or en brownfield ils appartiennent à l'**utilisateur** (le rsync d'adopt exclut ceux du template) → CI/tests/code client effacés puis commités. Double protection : **mode `--brownfield`** (aucun strip, deletes de profil confinés à `.claude/`, permissions et inventaires non purgés — le SKILL adopt le passe désormais, et `render --check` repasse AVANT le cleanup) **+ sentinelles de propriété** (`_is_template_owned` : un `.github/`/`test/`/`plugins/` homonyme sans marqueur template n'est **jamais** supprimé, même sans flag).
- **🔴 `prune_dead_permissions` effaçait des allow-rules vivantes** : globs (`.claude/hooks/*.py`) testés en chemin littéral, chemins `~/.claude/…` matchés en substring → supprimés à tort. Lookbehind d'ancrage + skip des chemins à métacaractères ; au doute on **garde** (une règle morte est inoffensive, une vivante supprimée = prompts en boucle).
- **🔴 Deny `.env` troué** : l'énumération laissait `.env.prod`, `.env.dev`… **silencieusement lisibles** via l'allow `Read(./**)`. Ajout du filet **`ask: Read(./.env.*)`** — fail-closed : tout `.env.*` non listé en deny déclenche un prompt ; `.env.example` lisible après 1 confirmation.
- **Projet généré propre** : `prune_bootstrap_inventory` purge les lignes `/init-from-template` + `/adopt-template` des index shippés (`.claude/CLAUDE.md`, `template-maintenance.md`, `USAGE.md`) ; sections « Garantie skills vitaux » / « affiner ensuite » réécrites (le cleanup **s'auto-retire**, décision de type AVANT exécution) ; vérif post-init sans `render.py` (grep) ; note marketplace sans liens locaux morts.
- **Rsync brownfield aligné** (adopt SKILL + USAGE) : exclut `EXAMPLES/`, `plugins/`, `.claude-plugin/` comme le greenfield.
- **`render.py`** : EXCLUDE += `plugins/` + `.claude-plugin/` (les exemples `{{ }}` n8n des plugins ne sont pas des placeholders).
- **CI durcie** : garde SendMessage tolère l'absence de `tools:` (héritage complet = conforme) ; check manifests **croisé** (sources présentes, `plugins/*` tous recensés, `name` plugin ↔ marketplace) ; références `/n8n-push` mortes nettoyées (STRUCTURE.md, exemple ACME ×3) ; entrée `adopt-template` redondante retirée de `SCRIPT_JETABLE`.

### Added

- **`test/test_cleanup.py`** (40 asserts, stdlib) + step CI : greenfield strippé/pruné, **homonymes protégés**, **brownfield intouché**, dry-run inerte — les 2 fonctions destructrices ne re-régresseront plus en silence.

## [0.9.0] — 2026-07-06

Composants stack → **plugins** (archi C incrémentale) : les capacités optionnelles sortent du scaffold standalone pour devenir des plugins installables par projet, **auto-découverts** par le harness → plus aucun inventaire `.md` à maintenir pour eux.

### Added

- **Marketplace** dans le repo (`.claude-plugin/marketplace.json`) + 2 plugins sous `plugins/` : **`n8n-expertise`** (les 7 skills n8n) et **`db-migration`** (Alembic), chacun avec `.claude-plugin/plugin.json` (`skills: "./skills/"`) + README. Install par projet : `/plugin marketplace add kurt83340/claude-Setup` puis `claude plugin install <plugin>@claude-setup --scope project` (skills namespacés `/<plugin>:<skill>`).
- **Check CI** « manifestes marketplace + plugins valides ».

### Changed

- **`cleanup-for-type.py`** : `automation-n8n`/`bdd-migration` ne copient plus de skills (retrait `copy_examples`/`copy_examples_glob` + les 2 fonctions de copie devenues mortes) ; `plugins/` + `.claude-plugin/` ajoutés au strip des artefacts de maintenance (le projet **installe** depuis le marketplace, il n'embarque pas la source).
- **`EXAMPLES/skills-n8n/` + `EXAMPLES/skills-db/` supprimés** (déplacés dans `plugins/`) → `EXAMPLES/` ne garde que l'exemple ACME. Le rsync d'init exclut désormais `plugins/` + `.claude-plugin/`.
- Doc basculée « skills stack copiés depuis EXAMPLES » → « plugins » : init SKILL, `.claude/CLAUDE.md`, `.claude/skills/README.md`, `template-maintenance.md`, `STRUCTURE.md`, `USAGE.md`, README repo.

## [0.8.2] — 2026-07-06

### Added

- **Garde-fou CI « teammate → SendMessage »** — nouvelle étape CI + règle #4 dans `agents/README.md` : toute déf `.claude/agents/*.md` (hors subagent pur `doc-maintainer`) DOIT lister `SendMessage` dans `tools:`, sinon le build **échoue**. Empêche de recréer le bug v0.8.1 (teammate muet) en ajoutant un futur rôle — plus besoin d'y penser, l'oubli est attrapé automatiquement.

## [0.8.1] — 2026-07-06

### Fixed

- **Teammates muets : `SendMessage` absent des défs d'agents** — spawné **nommé**, un agent tourne en **teammate** (session à boîte aux lettres) et son texte final ne remonte PAS au lead : le seul canal est l'outil `SendMessage`. Or **aucune** déf `agents/*.md` ne le listait dans son `tools:` (bug révélé par les explorateurs de `/conception` spawnés nommés → rapport évaporé, idle muet, zombie qui ping). `SendMessage` ajouté aux **8 rôles teammate** (`worker`, `front-end`, `back-end`, `tester`, `reviewer`, `explore-code`, `explore-docs`, `explore-memoire`) + garde-fou dans `.claude/rules/agent-teams.md` (§ intro). `doc-maintainer` (subagent pur, jamais teammate) laissé tel quel.

## [0.8.0] — 2026-07-06

Hygiène d'init : un projet **généré** ne doit hériter d'**aucun** artefact de maintenance du template — sinon sa CI casse (elle teste des chemins que l'init supprime) et il traîne du cruft.

### Changed

- **`cleanup-for-type.py` retire les artefacts de maintenance DU template pour TOUS les types** (nouveau `TEMPLATE_MAINTENANCE` + `strip_template_maintenance`) : `.github/` (self-CI qui testait `render.py` / `EXAMPLES` / l'inventaire des skills → **CI rouge héritée**, la cause racine), `test/`, `EXAMPLES/` (après copie des skills stack) et les skills bootstrap `adopt-template` + `init-from-template` (retiré **en dernier** — il contient le script). Résultat : le projet généré démarre **propre, sans CI héritée**.
- **Suppression déplacée du shell vers Python** : le SKILL `init-from-template` ne fait plus de `rm -rf` / `git rm` à la main (Étape 4 = simple `git add -A` + commit) — tout passe par `shutil.rmtree` dans `cleanup-for-type.py`, donc plus jamais bloqué par la règle `deny Bash(rm -rf:*)` (source de refus + retries à chaque init).
- Nouveau `prune_dead_permissions` : purge de `settings.json` les allow-rules pointant vers un script `.claude/…` supprimé (ex. les 2 règles `init-from-template` render/cleanup, mortes une fois le skill bootstrap retiré).

### Fixed

- **`settings.json` : deny `Read(./.env.*)` trop large** — il bloquait aussi `.env.example` (fichier template sain, committé). Remplacé par un set énuméré (`.env`, `.env.local`, `.env.*.local`, `.env.{development,staging,production,test}`) : les vrais secrets restent bloqués, `.env.example` / `.sample` / `.template` redeviennent lisibles.

## [0.7.0] — 2026-07-06

### Changed

- **Skills n8n hors-cœur remplacés** : les 3 skills d'exemple « jouets » (`n8n-push`, `n8n-seed-db`, `n8n-deploy` — déploiement) laissent place à **7 skills d'expertise n8n réels** dans `EXAMPLES/skills-n8n/` : `n8n-node-configuration`, `n8n-validation-expert`, `n8n-workflow-patterns`, `n8n-code-javascript`, `n8n-code-python`, `n8n-expression-syntax`, `n8n-mcp-tools-expert` (skills de référence auto-invoqués, avec fichiers de support type `DEPENDENCIES.md` / `OPERATION_PATTERNS.md`). Toujours copiés dans `.claude/skills/` par `/init-from-template` (type `automation-n8n`).
- **`cleanup-for-type.py`** : la copie des skills n8n passe d'un **mapping en dur** (3 entrées) à un **glob** `EXAMPLES/skills-n8n/n8n-*` (nouvelle clé de profil `copy_examples_glob` + fonction `copy_glob_from_examples`) → robuste à l'ajout/retrait de skills n8n sans toucher le script.
- Inventaires & doc synchronisés : `.claude/CLAUDE.md`, `.claude/rules/template-maintenance.md`, `USAGE.md`, `.github/README.md`, `EXAMPLES/skills-n8n/README.md`, `.env.example`, `workflows/README.md`.

## [0.6.0] — 2026-07-05

### Added

- **Skill `/adopt-template`** (14e skill cœur) — pendant **brownfield** de `/init-from-template` : greffe le template sur un projet EXISTANT sans jamais rien écraser. Copie via `rsync --ignore-existing` (l'existant gagne toujours), état des lieux détecté (manifests → stack + commandes pré-remplies), merges **diff-par-diff** des collisions (CLAUDE.md user préservé + index just-in-time, settings.json fusionné, .gitignore append), mêmes scripts render/cleanup que l'init (source unique), puis **rétro-remplissage** de la doc depuis le projet : stack.md ← manifests, code-map ← `/codemap`, cadrage ← README existant, ROADMAP ← Phase 0 + scan TODO/FIXME, HANDOFF ← git log, ADRs rétroactifs optionnels (max 2-3 — pas d'archéologie).

### Changed

- Inventaires synchronisés (14 skills cœur) ; `cleanup-for-type.py` : `script-jetable` retire aussi `/adopt-template` ; USAGE § « Projet EXISTANT (brownfield) » ; README repo (variante brownfield).

## [0.5.0] — 2026-07-05

Les « templates d'orchestration » : la chaîne implémentation existait déjà (`/spec` → `/conception` → `/team` → `/feature-done`, chaque maillon suggère le suivant) — cette version ajoute les chaînons manquants + le pipeline debugging.

### Added

- **Skill `/debug "<symptôme>"`** (13e skill cœur) — pipeline debugging : symptôme **verbatim** → REPRODUIRE (test rouge minimal — règle d'or : pas de repro = pas de fix) → explorer (`explore-code` + git log + `explore-memoire`) → hypothèses **discriminées par instrumentation** → fix minimal (la cause, pas le symptôme, sans refacto opportuniste) → suite verte → pérenniser (le test de repro RESTE, `/lecon`, gotcha code-map, CHANGELOG Fixed).
- **Mode TDD dans `/team`** (opt-in, décidé au plan d'équipe) : tasks de tests créées d'abord (assignées à `tester`), tasks d'implémentation **bloquées dessus** (`addBlockedBy`) — back/front font passer au vert sans modifier les tests.
- **Étape PR GitHub dans `/feature-done`** : `gh pr create` selon git-workflow (1 spec = 1 PR, squash, CI verte) ; `git push` reste en permission « ask » ; fallback commit local + tag.
- **Choix SDD/TDD critérisé dans `/conception`** (étape 4) : le mode d'exécution est décidé PAR SPEC et noté dans `plan.md` § Décisions — TDD si comportements spécifiables a priori (logique métier, parsing, contrats d'API) ; tests-après + E2E ciblés si exploratoire — `/team` lit ce choix.

### Changed

- Inventaires synchronisés (13 skills cœur) ; `cleanup-for-type.py` : `script-jetable` retire aussi `/debug`.

## [0.4.0] — 2026-07-05

### Added

- **3 agents explorateurs réutilisables** (lecture seule) : `explore-code` (patterns/points d'intégration en `chemin:ligne`), `explore-docs` (doc officielle à jour — context7 → MCP docs → web, URLs + versions, jamais de mémoire), `explore-memoire` (ADRs/leçons/idées/cadrage — « qu'a-t-on déjà décidé/tenté ? »). Le rôle et le format de rapport vivent dans la définition (source unique) ; `/conception` ne fournit que le brief par spec. Subagents par défaut, teammates en mode visible, invocables hors `/conception` pour toute investigation. Justification : `/conception` tourne à chaque spec → le seuil create-on-demand de réutilisation est atteint par construction.

### Changed

- `reviewer` : couvre explicitement la **revue adverse de plans** (`/conception` étape 5) en plus des diffs.
- Interaction directe user ↔ teammate **vérifiée sur doc officielle** et encodée : l'utilisateur peut répondre dans le pane d'un teammate (les gates de `/conception` peuvent s'y jouer) ; question utilisateur = texte dans le pane + `SendMessage` au lead « en attente décision » ; les prompts de permission remontent TOUJOURS au lead.
- Inventaires synchronisés (9 agents) : `agents/README`, `.claude/CLAUDE.md`, `template-maintenance.md`, rule `agent-teams.md`, `STRUCTURE.md`, README repo. (La variante « planifier dans un pane dédié » reste documentée dans `/conception` § Mode visible — via teammate **ad-hoc**, sans agent supplémentaire.)

## [0.3.0] — 2026-07-05

### Added

- **Skill `/conception <spec-id|macro>`** (12e skill cœur) — le workflow de planification arrêté qui manquait entre `/spec` (scaffold) et `/team` (exécution) : contraintes d'abord (code-map/ADR/leçons), **explorations parallèles par subagents** (code, docs officielles, mémoire projet — rapports sourcés), **2-3 options avec trade-offs** (jamais une seule), décision par l'utilisateur (ADR si structurante), plan avec **un point de vérification exécutable par étape**, tasks **partitionnées par fichiers** (prêtes pour `/team`), **revue adverse à contexte frais**, gel + ROADMAP/HANDOFF. Zéro nouveau type de fichier (remplit research/spec/plan/tasks existants), zéro nouvel agent (le skill est le foyer et orchestre des subagents — doctrine post-audit).

### Changed

- `/spec` : les « prochaines étapes » pointent vers `/conception` (au lieu de « remplir les 4 fichiers à la main »).
- Inventaires synchronisés (12 skills cœur) : `.claude/CLAUDE.md`, `template-maintenance.md`, `USAGE.md` (cheat-sheet + workflow feature complète), `STRUCTURE.md`, README repo ; `cleanup-for-type.py` (le type `script-jetable` retire aussi `/conception`).

## [0.2.1] — 2026-07-05

### Fixed

- **`render.py` (init-from-template) : init silencieusement à vide** — les motifs `EXCLUDE` étaient testés en substring sur le chemin **absolu** ; un projet situé sous un dossier parent nommé comme un motif (ex. `.../test/projetA/`) voyait 100 % de ses fichiers exclus → « 0 fichiers à scanner », 0 substitution, aucune erreur. Découvert au **premier init réel** (projetA, session satellite) et rapatrié ici. Correctif : matching sur le chemin **relatif** à la racine, **ancré sur les frontières de segments** (`latest/` ne matche plus `test/`). Test de régression `test/test_render.py` + step CI.

## [0.2.0] — 2026-07-05

Câblage **agent-teams** complet + **filets mémoire** — objectifs : tout déléguer à des agents visibles sous tmux (préconfigurés ou à la volée, retours à l'orchestrateur), mémoire cross-session qui n'oublie rien.

### Added

- **Agent teams câblés** dans `settings.json` : `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"` + `teammateMode: "tmux"` (split panes) ; permissions `git worktree` (add/list/prune en allow ; remove + merge en ask).
- **Rule `.claude/rules/agent-teams.md`** — SOURCE UNIQUE du protocole d'équipe, auto-chargée par toute session (lead ET teammates, y compris ad-hoc) : § Teammate (SendMessage avant idle, périmètre, docs partagés interdits, jamais committer HANDOFF.md), § Lead (politique teammate vs subagent, worktrees, task list native, débrief mémoire OBLIGATOIRE), **cycle de vie lead-owned vs user-owned** (un teammate demandé par l'utilisateur persiste, seul l'utilisateur le ferme ; un teammate auto-invoqué est fermé par le lead après débrief), **topologie hub-and-spoke par défaut / mesh opt-in scopé** (fixée au spawn).
- **Skill `/team <spec-id>`** (11e skill cœur) : préflight → plan d'équipe **validé par l'utilisateur** (rôles + topologie) → tasks natives (miroir de `specs/00X/tasks.md`) → 1 worktree par codeur → spawn → suivi (idle notifications + task list + trace) → **débrief mémoire à chaque rapport** → merge + tests après chaque merge → clôture propre.
- **4 rôles teammate préconfigurés** : `front-end`, `back-end`, `tester`, `reviewer` (lecture seule) — chaque fichier ne porte que sa spécialité, le protocole vient de la rule ; `worker.md` aminci de même (fin de la duplication).
- **Filet « n'oublie rien »** : hook `SessionEnd` (`sessionend-snapshot.py`) snapshotte l'état à CHAQUE fin de session ; `SessionStart(startup)` injecte le filet s'il est plus frais que `HANDOFF.md` (= `/handoff` oublié) puis le **consomme**.
- **Trace d'équipe** : hooks `TaskCreated`/`TaskCompleted`/`TeammateIdle` → `teamtask-log.py` → `.claude/.cache/team-progress.log` (1 ligne JSON/événement, jamais bloquant).
- **`/doc-health` étape 10 — auto-memory** : localise `MEMORY.md` (machine-locale, keyée par repo git — partagée par les worktrees), propose la **promotion** des patterns stables en rule / leçon / ADR (consolidation cache → docs versionnées).
- `snapshot_common.py` : helpers partagés PreCompact/SessionEnd (source unique du format snapshot).
- Suite de tests hooks étendue → **40 tests** (sessionend ×3, injection startup ×5, routing compact, teamtask-log ×5).

### Changed

- `template-maintenance.md` : § Agent teams remplacé par un pointeur vers la rule (single-source) ; § 3 layers enrichi — auto-memory = **cache** (machine-local, écrit en concurrence) → durabilité par promotion via `/doc-health`.
- Inventaires synchronisés : `.claude/CLAUDE.md` (11 skills cœur + roster agents), `USAGE.md` (cheat-sheet, table hooks, § Agent teams), `STRUCTURE.md` (arbres rules/skills/agents), `agents/README.md` (invocation subagent OU teammate), README repo.
- `cleanup-for-type.py` : le type `script-jetable` retire aussi `.claude/skills/team/`.

### Fixed

- Frontmatter `/lecon` : un « : » dans la description cassait le YAML strict (le parser Claude Code le tolère, mais fragile) → remplacé par un tiret.

## [0.1.0] — 2026-06-28

Première mise sous version, après audit complet (cf. `test/AUDIT-2026-06-28.md`).

### Added

- Repo GitHub privé `kurt83340/claude-Setup` + mise sous git.
- Suite de tests des hooks `test/test_hooks.py` (16 tests, stdlib, 0 dépendance).
- Proto de packaging plugin `test/build-plugin.py` (assemble un plugin distribuable, non-destructif).
- Rapport d'audit vérifié `test/AUDIT-2026-06-28.md`.
- CI GitHub Actions (tests hooks + validations structurelles à chaque push).

### Changed

- `CLAUDE.md` → **index just-in-time** : 3 `@-import` (HANDOFF/ROADMAP/code-map) au lieu de 18 ; reste lu à la demande. Mesuré : **~14,6k → ~1,5k tokens** auto-chargés au démarrage (−90 %).
- Hook PreCompact → snapshot dans `.claude/.cache/` (non-versionné, overwrite) au lieu d'être appendé au `HANDOFF.md` versionné. Fin du gonflement (+442 o/compaction avant).
- Réfs GitHub Spec Kit corrigées : `uv tool install specify-cli --from git+…@vX.Y.Z` + commandes `/speckit.*` (au lieu de `npx specify init`).

### Fixed

- `db-migration` : ajout `allowed-tools` + `disable-model-invocation` (frontmatter hors-norme).
- Permissions `/init-from-template` (`python3` scopé / `chmod` / `git init`) et `/spec` (`Bash(cp:*)`) → fin des prompts de permission pendant ces workflows.
- Retrait de la clé de réglage inerte `autoMemory.scope` (seuls `autoMemoryEnabled` / `autoMemoryDirectory` existent).

### Notes

- 2 pistes de l'audit initial **invalidées** après vérification sur la doc officielle : le layout skills à plat est correct (pas de scan récursif pour le regroupement) ; les schémas de hooks (`systemMessage`, stdout SessionStart) sont valides.
