---
name: handoff
description: Met à jour .claude/docs/HANDOFF.md à la fin d'une session de travail. Génère un snapshot narratif court (status + échecs tentés + blockers + next steps) à partir du git status + tests + contexte chat courant. À invoquer à chaque fin de session pour préserver l'état entre sessions Claude Code.
allowed-tools: Read, Write, Edit, Bash(git status), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(pytest:*), Bash(npm test:*), Bash(ruff:*)
disable-model-invocation: false
---

# /handoff — Snapshot fin de session

> **Quand ne PAS utiliser** : reprendre une session précise → `/resume` (natif, fidélité 100%) ·
> feature terminée à livrer → `/feature-done` · pattern technique appris → auto-memory ou `/lecon`.
> **Réversibilité** : 🟢 n'écrit que `.claude/docs/HANDOFF.md`, après confirmation —
> undo : `git checkout -- .claude/docs/HANDOFF.md`.

Ton rôle : générer une mise à jour propre de `.claude/docs/HANDOFF.md` qui permettra de reprendre le travail demain sans perdre le contexte.

## Étape 1 — Collecter l'état actuel

Lance en parallèle :

```bash
git status
git log -5 --oneline
git diff --stat main
git branch --show-current
```

Si projet Python : `pytest --tb=no -q | tail -10` (rapide)
Si projet Node : `npm test -- --silent` (rapide)

## Étape 2 — Lire le HANDOFF actuel + détecter "fresh"

Lis `.claude/docs/HANDOFF.md`.

**Détection "fresh"** : si le fichier contient > 5 placeholders `{{...}}` non substitués → considérer comme HANDOFF initial (post-init template), **ne PAS préserver de sections custom** (il n'y en a pas). Générer un HANDOFF complet from scratch en Étape 3.

```bash
PLACEHOLDERS=$(grep -cE '\{\{[^}]+\}\}' .claude/docs/HANDOFF.md)
if [ "$PLACEHOLDERS" -gt 5 ]; then
  echo "📝 HANDOFF fresh détecté ($PLACEHOLDERS placeholders) → regen complet"
fi
```

Sinon (HANDOFF déjà rempli) : préserver les sections custom du user (heuristique : tout ce qui n'est pas dans le format standard).

## Étape 3 — Composer le nouveau HANDOFF

Format strict :

```markdown
# HANDOFF — YYYY-MM-DD HHhMM

> Court, narratif, versionné. Patterns techniques → auto-memory. Reprise précise → /resume.

**Branche** : `<branch>`
**Spec en cours** : [<spec-name>](conception/specs/<spec>/spec.md) (X/Y tasks)
**Goal session** : <ce que je voulais faire>

## Status

- ✅/⏳/❌ <test command> : <résultat>
- ✅/⏳ <lint/type check> : <résultat>
- ✅/⏳ <autre check>

## Échecs tentés (à ne pas refaire)

- <approche A tentée> → <pourquoi KO>
- <approche B> → <pourquoi rejetée>

## Blocked on

- <bloqueur 1>
- <bloqueur 2>

## Next (par ordre)

1. **Task #N** : <description courte>
2. **Task #N+1** : ...
3. <étape suivante>

## Continuation State (machine-readable — grammaire fixe `Clé: valeur`, 1 ligne chacune)

Spec: <00X-slug | aucune>
Task: <T2.3 | aucune>
Fichiers en cours: <chemins séparés par virgule | aucun>
Bloqué sur: <rien | description courte>
Commande de reprise: <la 1re commande à lancer en reprenant | aucune>

## Journal (append-only — 1 ligne par session, NE JAMAIS réécrire)

- YYYY-MM-DD — <ce qui a été fait cette session, en 1 phrase>
```

> Le **Continuation State** duplique volontairement l'essentiel de « Next » en grammaire fixe :
> c'est le point de reprise **parseable** (par un agent frais ou un script) quand la prose ambiguë
> coûte cher. Toujours les 5 clés, même à `aucune` — une clé absente est indistinguable d'un oubli.

## Étape 4 — Présenter le diff au user

⚠️ **NE PAS écrire directement**. Présenter d'abord le diff proposé :

```
📋 Nouveau HANDOFF proposé :

<diff colorisé>

OK pour écrire ? (yes/edit/cancel)
```

Si user confirme → Write. Sinon → ajuster selon ses retours.

## Étape 5 — Bonus

Si feature livrée (toutes tasks ✅) :

- Suggérer d'enchaîner avec `/feature-done <spec-id>`

Si > 3 décisions tech récentes sans ADR :

- Suggérer `/lecon` pour capturer

Si HANDOFF n'a pas changé (rien de neuf) :

- Skip l'écriture, juste timestamp update

## Anti-patterns à éviter

- ❌ Écrire un roman (HANDOFF court = < 30 lignes ; le **Journal** est l'exception : il gagne 1 ligne/session)
- ❌ Réécrire/écraser le **Journal** : on APPEND seulement (1 ligne/session) → l'arc complet reste reconstructible depuis le seul HANDOFF
- ❌ Dupliquer ce qui est déjà dans CHANGELOG (factuel) ou auto-memory (patterns)
- ❌ Lister TOUS les commits (juste le sens général)
- ❌ Mentionner des credentials/secrets

## Note : invocation par hook PreCompact

Ce skill est aussi déclenché **automatiquement** par le hook `PreCompact` (avant compaction du contexte) qui appelle `.claude/hooks/precompact-snapshot-handoff.py`. Le hook fait un snapshot minimal (timestamp + git state + last messages) sans demande de confirmation. Le skill `/handoff` est la version manuelle riche (avec review user).

## Note : invocation par agent doc-maintainer

L'agent `doc-maintainer` (Task tool) peut aussi générer le HANDOFF en mode "scan auto + propose tout". Utilise l'agent quand tu veux un workflow complet (HANDOFF + ROADMAP + CHANGELOG synchronisés). Utilise `/handoff` quand tu veux juste mettre à jour HANDOFF rapidement.

## Note : projets script-jetable

Sur un projet initialisé en `script-jetable`, `/feature-done` et l'agent `doc-maintainer` ne sont **pas installés** (cleanup). Ce skill reste pleinement autonome (aucune dépendance) — ignore simplement la suggestion `/feature-done` (Étape 5) sur ce type de projet.
