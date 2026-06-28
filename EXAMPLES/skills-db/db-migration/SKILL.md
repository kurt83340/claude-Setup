---
name: db-migration
description: Crée une nouvelle migration Alembic, applique-la en local, et update la doc. À utiliser quand l'utilisateur veut modifier le schéma BDD (ajouter colonne, table, index).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(alembic:*), Bash(pytest:*), Bash(git status), Bash(git diff:*), Bash(date:*)
disable-model-invocation: false
---

# /db-migration — Workflow migration BDD (Alembic)

Workflow standardisé pour créer une migration Alembic propre.

> 📦 **Skill stack-spécifique** (Alembic / SQLAlchemy) — vit dans `EXAMPLES/` et n'est PAS
> dans le cœur du template. Copié dans `.claude/skills/` par `/init-from-template` (type
> `bdd-migration`), ou à la main : `cp -r EXAMPLES/skills-db/db-migration .claude/skills/`.

## Étapes

1. **Comprendre le besoin** : demande quelle modif de schéma (colonne, table, contrainte ?)

2. **Vérifier l'état actuel** :

   ```bash
   alembic current
   alembic history --verbose | head -20
   ```

3. **Créer la migration auto-générée** :

   ```bash
   alembic revision --autogenerate -m "<description courte>"
   ```

4. **Lire et review le fichier généré** :
   - Path : `alembic/versions/<hash>_<description>.py`
   - Vérifier : `upgrade()` ET `downgrade()` cohérents
   - Si autogénération a raté un truc (index, contrainte), l'ajouter manuellement

5. **Tester en local** :

   ```bash
   alembic upgrade head
   pytest tests/integration/
   alembic downgrade -1  # vérifier que le downgrade marche
   alembic upgrade head
   ```

6. **Si migration structurante (table, colonne required, drop)** :
   - Créer un ADR : `.claude/docs/adr/00XX-infra-migration-<description>.md` (scope `infra`)
   - Update `.claude/docs/adr/README.md` table scope `infra`
   - Ajouter une entry dans `.claude/docs/CHANGELOG.md` section `Decided` avec lien ADR

7. **Update RUNBOOK** si la migration nécessite des précautions prod (lock long, downtime) :
   - Section "Migrations prod" dans `.claude/docs/RUNBOOK.md`

## Règles

- ❌ JAMAIS `DROP COLUMN` direct → toujours 2 migrations (deprecate + drop dans v+1)
- ❌ JAMAIS de migration sans `downgrade()` fonctionnel
- ✅ TOUJOURS tester upgrade + downgrade en local avant push
- ✅ ADR si migration > 100k rows (impact perf)
