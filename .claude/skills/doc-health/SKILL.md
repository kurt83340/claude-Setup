---
name: doc-health
description: Audit hebdo de la santé du template doc. Vérifie fraîcheur HANDOFF, ADRs manquants pour décisions tech, growth opportunities (ACCESS/RUNBOOK à créer), drift code-map vs code réel, leçons en attente de décision. Génère un rapport priorisé sans modifier.
allowed-tools: Read, Glob, Grep, Bash(find:*), Bash(stat:*), Bash(git log:*), Bash(date:*)
disable-model-invocation: false
---

# /doc-health — Audit hebdomadaire du template

Ton rôle : scanner la santé documentaire du projet et produire un rapport actionnable.

## Étape 1 — Fraîcheur des fichiers vivants

```bash
# Date de dernière modif des fichiers vivants
stat -c "%y %n" .claude/docs/HANDOFF.md
stat -c "%y %n" .claude/docs/ROADMAP.md
stat -c "%y %n" .claude/docs/CHANGELOG.md
stat -c "%y %n" .claude/docs/ACCESS.md
stat -c "%y %n" .claude/docs/cadrage/README.md
```

Seuils :
| Fichier | Vert | 🟠 Orange | 🔴 Rouge |
|---|---|---|---|
| .claude/docs/HANDOFF.md | < 3j | 3-7j | > 7j |
| .claude/docs/ROADMAP.md | < 7j | 7-14j | > 14j |
| .claude/docs/CHANGELOG.md | < 14j (si livraison récente) | — | > 30j sans entry |
| .claude/docs/ACCESS.md | — | — | > 30j (peut-être obsolète) |

## Étape 2 — Growth opportunities

Détecter les triggers de création de nouveaux fichiers :

```bash
# Credentials/API/OAuth mentionnés sans .claude/docs/ACCESS.md riche
grep -rE "API_KEY|token|secret|OAuth|credentials" .claude/docs/conception/ src/ 2>/dev/null | head -5

# Mentions de déploiement/prod sans .claude/docs/RUNBOOK.md
grep -rE "deploy|prod|production|incident|rollback" .claude/docs/conception/ src/ 2>/dev/null | head -5

# Termes métier répétés sans GLOSSARY enrichi
# (heuristique : mots en majuscules ou jargons spécifiques détectés > 3 fois)
```

Si triggers détectés ET fichier vide/minimal :

- 🟢 Suggérer d'enrichir .claude/docs/ACCESS.md / .claude/docs/RUNBOOK.md / .claude/docs/GLOSSARY.md

## Étape 2bis — Review `.growth-suggestions.md` (auto-flag du hook PostToolUse)

Le hook PostToolUse écrit dans `.claude/.growth-suggestions.md` à chaque détection de growth trigger pendant les Edit/Write. Ce fichier peut grossir indéfiniment sans review.

```bash
# Lire les suggestions auto-flag
if [ -f .claude/.growth-suggestions.md ]; then
  ENTRIES=$(grep -c "^-" .claude/.growth-suggestions.md)
  AGE_DAYS=$((($(date +%s) - $(stat -c %Y .claude/.growth-suggestions.md)) / 86400))
  echo "📝 $ENTRIES suggestions auto-flag, dernière MAJ il y a ${AGE_DAYS}j"
fi
```

**Reporter dans le rapport** :

- Si > 10 entries → 🟠 "Review et trie : action OU discard. Tronquer le fichier après."
- Si > 30 entries → 🔴 "Backlog growth important, action urgente"

**Action proposée à l'user** : pour chaque entry, soit `→ action (créer .claude/docs/ACCESS.md, etc.)` soit `→ discard` (ajouter ligne `~~strikethrough~~` dans le fichier).

Quand toutes les entries sont actées/discardées : truncate le fichier (garder le header).

## Étape 3 — ADRs manquants

```bash
# Compter les "choisi", "retenu", "vs", "plutôt que" dans plan.md sans ADR créé récemment
grep -rE "choisi|retenu|plutôt que|vs " .claude/docs/conception/specs/*/plan.md 2>/dev/null | wc -l

# Compter les ADRs créés ce mois
find .claude/docs/adr/ -name "*.md" -newer "$(date -d '1 month ago' +%Y-%m-%d)" 2>/dev/null | wc -l
```

Si ratio décisions/ADRs > 5 → suggérer de promouvoir.

## Étape 4 — Leçons en attente de décision

```bash
# Entries .claude/docs/lecons.md avec status 🆕 new
# (+ repérer celles datées > 14j via les headers ## YYYY-MM-DD —)
grep -c "status:.*🆕 new" .claude/docs/lecons.md
```

- Si > 5 entries `🆕 new` → 🟢 review hebdo (`/lecon promote` / `discard`)
- Si une `🆕 new` date de > 14j → 🟠 "en attente de décision depuis > 14j → review urgent"

## Étape 5 — Drift code-map vs code

```bash
# Date code-map vs date dernier commit dans src/
stat -c %Y .claude/docs/code-map.md
git log -1 --format=%ct -- src/ 2>/dev/null
```

Si dernier commit src/ > date code-map → 🟠 "code-map peut être stale, lancer /codemap pour resync"

## Étape 6 — Sections cassées / TODO non remplis

```bash
# Placeholders non remplis ({{...}})
grep -rE "\{\{[^}]+\}\}" .claude/docs/ | head -10

# TODO non décrochés
grep -rE "^- \[ \].*TODO|TODO :" .claude/docs/ | head -10
```

## Étape 7 — ADRs sans status valide

```bash
# ADRs où le frontmatter status manque ou est vide
for f in .claude/docs/adr/[0-9]*.md; do
  if ! grep -q "^status:" "$f"; then
    echo "🔴 $f : pas de status"
  fi
done

# ADRs status: superseded mais pas archivés dans le README
grep -l "^status: superseded" .claude/docs/adr/[0-9]*.md 2>/dev/null
# Vérifier que chacun est listé dans la section "archived / superseded" du README
```

## Étape 8 — Specs stalled + liens ROADMAP cassés

```bash
# Specs marquées [~] EN COURS dans ROADMAP mais pas de commit récent
grep -E "\[~\].*EN COURS" .claude/docs/ROADMAP.md
# Pour chaque spec en cours, vérifier la dernière modif des fichiers
find .claude/docs/conception/specs/*/tasks.md -mtime +30 2>/dev/null

# Liens spec cassés : chaque spec référencée dans ROADMAP doit exister sur disque
grep -oE "conception/specs/[0-9a-z-]+/spec\.md" .claude/docs/ROADMAP.md | while read -r p; do
  [ -f ".claude/docs/$p" ] || echo "🔴 ROADMAP référence une spec absente : $p"
done
```

- Si `[~]` depuis > 30j → 🟠 "spec stalled, refresh ou archive"
- Si spec référencée absente → 🔴 "lien ROADMAP cassé"

## Étape 9 — Idées âgées sans décision

```bash
# Idées dans idees/ > 30 jours sans status décidé
find .claude/docs/idees/ -name "*.md" -mtime +30 2>/dev/null | head -10
```

Si > 5 idées vieilles → 🟢 "review idées : promouvoir / discard / archiver"

## Étape 10 — Rapport synthétique

Format type :

```markdown
# 📊 Doc Health Report — YYYY-MM-DD

## 🔴 Critique (à faire cette semaine)

- .claude/docs/HANDOFF.md > 7 jours (dernière MAJ 2026-05-15) → lancer /handoff
- 8 entries .claude/docs/lecons.md statut 🆕 new → review + promotion

## 🟠 Attention

- .claude/docs/code-map.md pas MAJ depuis le dernier refacto (commit abc123) → /codemap
- .claude/docs/ROADMAP.md ligne `[~] 002-notion-writer` en cours depuis 14j → status réel ?

## 🟢 Suggestions

- 5 mentions de "API_KEY" dans plan.md mais .claude/docs/ACCESS.md vide → enrichir ?
- 3 "choisi vs" dans 001/plan.md sans ADR → promouvoir en ADR ?
- 2 placeholders {{...}} non remplis (CLAUDE.md ligne 12, README.md ligne 8)

## ✅ Tout va bien

- .claude/docs/CHANGELOG.md à jour (dernière entry 2026-05-22)
- Pas d'ADR superseded sans archivage
- Glossary à jour
```

## Anti-patterns

- ❌ Modifier les fichiers (juste audit, pas write)
- ❌ Reporter sans priorité (toujours 🔴/🟠/🟢)
- ❌ Faux positifs (vérifier que le fichier est vraiment stale, pas juste pas modifié)
- ❌ Bloquer sur un seul check (continuer le scan même si une étape échoue)

## Note : invocation par agent doc-maintainer

Le skill `/doc-health` est l'invocation manuelle directe. L'agent `doc-maintainer` (Task tool) peut faire le même scan + proposer les diffs (vs juste rapporter). Utilise l'agent pour "scan + agir", utilise le skill pour "juste scanner".
