# Test Report — Template Claude Code

> Date : 2026-05-25
> Méthode : 3 scénarios représentatifs (A=script jetable, B=automation n8n, C=web app enterprise) initialisés avec `render.py` + simulation workflow.

> ⚠️ **Document historique** : ce rapport référence l'ancienne structure namespace (`memoireprojet/`). Depuis 2026-05-28, les skills et agents sont à plat (`.claude/skills/<nom>/`, `.claude/agents/<nom>.md`) car Claude Code ne scanne pas récursivement ([issue #18192](https://github.com/anthropics/claude-code/issues/18192)). Le script `validate-namespaces.py` a été supprimé. **⚠️ Ne pas se fier à ce rapport pour l'état actuel du template** (chemins `memoireprojet/` + chiffres périmés) — conservé uniquement comme trace d'itération historique. Statut backlog : **F6** (promote leçon/idée) est **résolu** via les modes `/lecon promote` & `/idee promote` ; **F9** (scaffold `STAKEHOLDERS.md`) reste **ouvert**.

## Setup test

| Scénario | Projet                             | Type           | Stack imaginaire     |
| -------- | ---------------------------------- | -------------- | -------------------- |
| **A**    | Migration CSV→SQLite (Boulangerie) | script-jetable | Python + pandas      |
| **B**    | Sync Prestashop→Sage (Distri Sud)  | automation-n8n | n8n + Python helpers |
| **C**    | Dashboard Sales (MegaCorp)         | web-app        | Next.js + Postgres   |

## Résultats bruts

| Mesure                                    | A   | B   | C   |
| ----------------------------------------- | --- | --- | --- |
| Fichiers copiés                           | 53  | 53  | 53  |
| Placeholders totaux                       | 374 | 374 | 374 |
| Substitutions auto via vars.json (7 vars) | 18  | 18  | 18  |
| Placeholders restants post-init           | 371 | 371 | 371 |
| Occurrences restantes (multiples par PH)  | 325 | 325 | 325 |

## 🔴 Frictions critiques

### F1. render.py ne distingue pas placeholders core vs content (374 vs 7)

**Symptôme** : après `/init-from-template`, 371 placeholders restent dans le projet → l'audit `/doc-health` les flag comme "à remplir" → 325+ faux positifs.

**Origine** : tous les placeholders utilisent le même format `{{...}}` — pas de différenciation entre :

- **CORE** (`{{PROJECT_NAME}}`, `{{CLIENT_NAME}}`) → substituables automatiquement
- **CONTENT** (`{{situation actuelle, douleurs}}`, `{{seuil}}`) → à remplir manuellement au fil de l'eau

**Impact** : noyade visuelle, l'user ne sait pas où concentrer son effort post-init.

**Fix proposé** :

- Convention : `{{UPPER_SNAKE_CASE}}` pour CORE, `{{libre minuscule}}` pour CONTENT
- `render.py` warn UNIQUEMENT sur les CORE non remplis
- `/doc-health` ignore les CONTENT placeholders, flag uniquement les CORE manquants
- Ajouter un check init "✅ Tous les CORE sont substitués"

### F2. Pas de skill `/spec <id> <titre>` pour scaffold une feature

**Symptôme** : à chaque nouvelle feature, l'user doit créer manuellement 4 fichiers : `research.md`, `spec.md`, `plan.md`, `tasks.md` dans `conception/specs/00X-titre/`.

**Origine** : les fichiers ne sont pas templatés dans le skill (ils n'existent que dans EXAMPLES, qui n'est PAS copié dans le projet final).

**Impact** : friction quotidienne sur le workflow le plus fréquent (= démarrer une feature).

**Fix proposé** : créer skill `/spec` qui :

1. Calcule le N suivant (max(existant) + 1)
2. Demande titre via AskUserQuestion
3. Crée les 4 fichiers depuis templates bundlés dans `.claude/skills/memoireprojet/spec/templates/`
4. Update ROADMAP.md (ajoute ligne `[ ] [00X-titre](...)`)

### F3. HANDOFF.md initial = que des placeholders → 1er `/handoff` bizarre

**Symptôme** : au tout premier `/handoff` d'un projet fraîchement init, le skill lit HANDOFF.md (rempli de `{{...}}`) et tente de préserver ses "sections custom" → composition d'un HANDOFF sur des bases bidons.

**Impact** : 1ère expérience cassée.

**Fix proposé** : `/handoff` étape 2, détecter si HANDOFF contient > 5 placeholders `{{...}}` → considérer comme "fresh", générer un HANDOFF complet sans préservation.

## 🟠 Frictions importantes

### F4. `/init-from-template` type=script-jetable ne nettoie pas vraiment

**Symptôme** : l'étape 4 dit "Supprimer 80% des docs si type=script-jetable" mais c'est de la doc, pas un script exécutable. L'user doit le faire à la main.

**Fix** : ajouter `scripts/cleanup-for-type.py` qui supprime vraiment les fichiers selon le type :

- `script-jetable` → garde `CLAUDE.md`, `cadrage/README.md`, `HANDOFF.md`, `CHANGELOG.md` ; supprime le reste
- `automation-n8n` → garde tout, supprime `RUNBOOK.md` (créé post-prod)
- `web-app` → garde tout, supprime `workflows/`

### F5. `/adr` ne propose pas la liste des ADRs existants

**Symptôme** : quand le skill demande "supersede un ADR existant ? (numéro)", l'user doit aller chercher la liste lui-même.

**Fix** : étape 2 du skill, scanner `adr/[0-9]*.md`, afficher la liste numérotée pour aider à choisir.

### F6. Pas de `/promote-lecon` ou `/promote-idee`

**Symptôme** : la promotion est documentée (lecons.md → ADR via /adr, idees/ → spec via /spec) mais aucun skill ne fait l'orchestration (créer ADR + update entry lecon en une commande).

**Fix** : créer 2 skills courts :

- `/promote-lecon <date> <decision>` → crée ADR avec contenu de la leçon + update status leçon
- `/promote-idee <date>` → crée spec via `/spec` + update status idée

### F7. Pas de `/pivot` dédié

**Symptôme** : workflow pivot 7-étapes documenté dans USAGE.md + agent doc-maintainer, mais aucun skill direct. L'user doit invoquer "Lance l'agent doc-maintainer pour faire un pivot".

**Fix** : créer `/pivot "<raison>"` qui orchestre les 7 étapes en demandant validation à chaque step.

## 🟢 Améliorations mineures

### F8. `.growth-suggestions.md` peut grossir indéfiniment

Pas de skill pour le réviser. `/doc-health` mentionne juste son existence.

**Fix** : intégrer une étape "review growth-suggestions" dans `/doc-health` étape 2bis.

### F9. Pas de scaffolding pour `STAKEHOLDERS.md` (scénario C)

Mentionné dans CLAUDE.md mais pas templaté. Quand l'user en a besoin (> 5 stakeholders), il doit l'inventer.

**Fix** : créer template `.claude/docs/STAKEHOLDERS.md.tmpl` (ou doc dans cadrage/README.md).

### F10. EXAMPLES/ jamais copié → /init Étape 4 confuse

L'étape 4 dit "Supprimer EXAMPLES/" mais EXAMPLES est dans le repo template, pas dans le projet user après copy/rsync.

**Fix** : clarifier dans le skill que EXAMPLES reste dans le template source.

## Conclusions

| Fix | Priorité | Effort | Impact |
| --- | -------- | ------ | ------ |
| F1  | 🔴       | M      | Haut   |
| F2  | 🔴       | M      | Haut   |
| F3  | 🔴       | S      | Moyen  |
| F4  | 🟠       | M      | Moyen  |
| F5  | 🟠       | S      | Moyen  |
| F6  | 🟠       | M      | Moyen  |
| F7  | 🟠       | M      | Moyen  |
| F8  | 🟢       | S      | Bas    |
| F9  | 🟢       | S      | Bas    |
| F10 | 🟢       | S      | Bas    |

**Itération 1** (immédiate) : F1, F2, F3, F5 ✅ FAIT
**Itération 2** (continuation) : F4, F7, F8, F10 ✅ FAIT
**Itération 3** (multi-namespace) : validate-namespaces.py + README skills/agents + section USAGE ✅ FAIT
**Backlog restant** : F6 (skills `/promote-lecon`, `/promote-idee`), F9 (scaffold STAKEHOLDERS.md) — non bloquants

## Itération 2 — fixes appliqués

### F4 — Cleanup adapté au type de projet ✅

**Script créé** : `.claude/skills/memoireprojet/init-from-template/scripts/cleanup-for-type.py`

- 5 profils : `script-jetable`, `automation-n8n`, `python-app`, `web-app`, `bdd-migration`
- Modes `--dry-run` et `--verbose`
- **Auto-fix** : retire les @-imports cassés de CLAUDE.md après suppression
- **Test script-jetable validé** : 53 → 25 fichiers (-53%), 10 → 3 skills, 5 → 3 hooks

### F7 — Skill `/pivot` orchestré ✅

**Skill créé** : `.claude/skills/memoireprojet/pivot/SKILL.md`

- Workflow 7 étapes : réunion → cadrage → research → PRD bump → tasks refonte → ROADMAP v2 → ADR + leçon
- Chaque étape demande validation user
- Détecte fichiers absents (gracieux si pas de PRD ou pas d'ADR)

### F8 — Growth review intégré dans `/doc-health` ✅

- Nouvelle Étape 2bis : lecture `.growth-suggestions.md` + seuils (>10 🟠, >30 🔴)
- Action proposée : trier entries OU truncate

### F10 — Clarification EXAMPLES ✅

- Étape 4 du `/init-from-template` : mention claire "EXAMPLES n'est PAS copié par défaut avec rsync --exclude"

## Itération 3 — Multi-namespace tooling ✅

**Préparation pour skills/agents futurs** depuis GitHub, MCP, autres repos.

### Validation collisions

**Script** : `.claude/skills/memoireprojet/init-from-template/scripts/validate-namespaces.py`

- Scan `.claude/skills/*/` et `.claude/agents/*/` récursivement
- Extrait `name:` du frontmatter de chaque
- Liste conflits + exit code 1
- **Test validé** : détecte conflit `name: handoff` entre namespaces différents

### Documentation namespace

- `.claude/skills/README.md` — convention + import GitHub/MCP/plugin
- `.claude/agents/README.md` — même convention pour agents
- Section USAGE.md "Validation des namespaces"

### Test multi-namespace ✅

Skill externe `n8n-validate` (namespace `n8n-community/`) cohabite proprement avec skills locaux `memoireprojet/`. Validation passe sans conflit.

## Vérification finale — petit ET gros projets vivent bien

| Mesure                     | Petit (script-jetable)  | Gros (web-app)             |
| -------------------------- | ----------------------- | -------------------------- |
| Fichiers .md final         | 3 docs vivants          | ~21 docs (toute la struct) |
| Skills disponibles         | 3 (handoff/lecon/init)  | 10 (tous)                  |
| Hooks                      | 3 (HANDOFF lifecycle)   | 5 (tous)                   |
| Agent                      | 0                       | 1 (doc-maintainer)         |
| Refs cassées post-cleanup  | ✅ 0                    | ✅ 0                       |
| CORE placeholders restants | ✅ 0                    | ✅ 0                       |
| Prêt pour skills externes  | ✅ namespace convention | ✅ namespace convention    |
