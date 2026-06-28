---
name: feature-done
description: Marque une feature comme livrée. Coche dans .claude/docs/ROADMAP.md, ajoute entry dans .claude/docs/CHANGELOG.md, met à jour .claude/docs/HANDOFF.md, suggère ADRs si décisions tech structurantes, vérifie que .claude/docs/code-map.md est à jour. À invoquer après livraison d'une feature (tous les tasks de specs/00X/tasks.md cochés).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git status), Bash(git log:*), Bash(git diff:*), Bash(date:*)
disable-model-invocation: false
---

# /feature-done — Livraison d'une feature

Ton rôle : finaliser proprement une feature en synchronisant tous les fichiers vivants.

## Usage

```
/feature-done <spec-id>
# Exemple : /feature-done 001-erp-connector
```

## Étape 1 — Vérifier la spec

1. Lire `.claude/docs/conception/specs/<spec-id>/tasks.md`
2. Vérifier que TOUS les tasks sont cochés `[x]`
3. Vérifier que le DoD est rempli
4. Si non → demander à l'user "Es-tu sûr que la feature est livrée ? Tasks restants : X, Y"

## Étape 2 — Détecter les décisions tech à promouvoir en ADR

Scan `.claude/docs/conception/specs/<spec-id>/plan.md` pour mots-clés :

- "choisi", "retenu", "vs", "plutôt que", "rejeté"
- "decision", "pattern", "lib"

Si trouvé → liste les décisions au user :

```
🔍 Décisions tech détectées dans plan.md :
1. "On choisit httpx au lieu de requests parce que…"
2. "Pattern retry avec tenacity (3x backoff)"

Promouvoir en ADR ?
- (a) ADR-00XX-feature-001-http-client (utile si lib réutilisée ailleurs)
- (b) ADR-00YY-feature-001-retry-pattern
- (c) Laisser dans plan.md (décisions trop locales)
```

**Règle décision** (cf `.claude/docs/adr/README.md`) :

- Décision **cross-feature** ou qui **survit à la feature** → ADR global (créer fichier)
- Décision **locale à cette feature uniquement** → laisser dans `plan.md` section `## Décisions`

## Étape 2bis — Si ADR créé : update `.claude/docs/adr/README.md`

Pour chaque ADR créé en étape 2 :

1. Créer le fichier `.claude/docs/adr/00XX-<scope>-<titre-court>.md` (format complet voir `.claude/docs/adr/README.md`)
2. Ajouter une ligne dans la table du scope correspondant dans `.claude/docs/adr/README.md` :
   ```markdown
   | [00XX](00XX-<scope>-<titre>.md) | <titre> | Accepted |
   ```
3. Si l'ADR **supersede** un ancien :
   - Update frontmatter de l'ancien : `status: superseded` + `superseded_by: 00XX`
   - Déplacer l'ancien vers la table "archived / superseded" dans le README

## Étape 2ter — Marquer les leçons promues

Si une décision provient d'une entry dans `.claude/docs/lecons.md` (status `🆕 new`) :

1. Trouver l'entry concernée (grep titre)
2. Update le status : `🆕 new` → `📜 → ADR-00XX` avec lien

## Étape 3 — Update .claude/docs/ROADMAP.md

Trouver la ligne `- [~] [<spec-id>](...) — **EN COURS** X/Y tasks` :

- Remplacer par `- [x] [<spec-id>](...) — livré YYYY-MM-DD`
- Retirer le **gras** (plus en cours)

## Étape 4 — Append entry dans .claude/docs/CHANGELOG.md

Format Keep a Changelog dans la section `## [Unreleased]` :

```markdown
### Added

- <nom feature> ([spec](conception/specs/<spec-id>/spec.md))
- Tests : X tests verts, coverage Y%

### Decided (si ADR créé)

- <titre décision> ([ADR-XXXX](adr/XXXX-...md))
```

## Étape 5 — Update .claude/docs/HANDOFF.md

Section "Status" :

- ✅ Feature `<spec-id>` livrée YYYY-MM-DD

Section "Next" :

- Suggérer la feature suivante (depuis ROADMAP)
- Ou suggérer phase suivante

## Étape 6 — Update .claude/docs/code-map.md (si applicable)

⚠️ Seulement si la feature a introduit du **non-déductible** : nouvelle règle de
couplage, contrainte d'archi, ou gotcha. Le rôle des fichiers / leurs imports / leurs
tests ne se documentent PAS ici (Claude les retrouve seul, et ça drifterait).

- Nouvelle **règle de couplage** (ex. « le nouveau module ne doit pas importer X ») ? → l'ajouter
- Nouveau **gotcha** rencontré pendant la feature ? → le noter (avec pointer `fichier:ligne`)
- Découpage en sous-systèmes changé ? → revoir la vue macro
- Présenter le diff au user ; si refacto large → `/codemap` (régénère macro + détecte violations)

## Étape 7 — Archiver les idées promues (si applicable)

Si la feature est issue d'une `.claude/docs/idees/YYYY-MM-DD-titre.md` :

1. Update le statut dans l'idée : `Statut: 💡 Backlog` → `✅ Promu en spec 00X — livré YYYY-MM-DD`
2. Optionnel : déplacer vers `.claude/docs/idees/archived/` (créer le dossier si besoin)

## Étape 8 — Suggérer commit + tag

```bash
git add .
git commit -m "feat(<spec-id>): <titre court>"

# Optionnel si release
git tag -a v$(date +%Y.%m.%d-%H%M) -m "Feature <spec-id> livrée"
```

## Sortie attendue

```
✅ Feature 001-erp-connector marquée comme livrée

📝 Fichiers mis à jour :
- .claude/docs/ROADMAP.md : [~] → [x] livré 2026-06-10
- .claude/docs/CHANGELOG.md : entry "Client SAP B1 (auth + fetch + pagination)" ajoutée
- .claude/docs/HANDOFF.md : status mis à jour
- .claude/docs/code-map.md : section sap_connector ajoutée

📚 ADRs proposés :
- ADR-0004-mvp-pattern-retry-tenacity ← user à valider

🚀 Suivant : démarrer feature 002-notion-writer ? (lance /spec ou créer manuellement)
```

## Anti-patterns

- ❌ Cocher [x] sans vérifier le DoD
- ❌ Promouvoir trop d'ADRs (chaque décision **locale** = pas un ADR — garder dans plan.md)
- ❌ Auto-commit sans demander
- ❌ Ajouter des descriptions fichier-par-fichier dans code-map.md (déductible — Claude le retrouve seul)
- ❌ Créer un ADR sans update `.claude/docs/adr/README.md` (index par scope)
- ❌ Oublier de marquer la leçon source (status `🆕 new` → `📜 → ADR-00XX`)

## Note : invocation par agent doc-maintainer

Tu peux aussi déléguer ce workflow à l'agent `doc-maintainer` (Task tool) qui scanne l'état + propose tous les diffs en une fois. Le skill `/feature-done` est l'invocation manuelle directe ; l'agent est la version "scan auto + tout proposer".
