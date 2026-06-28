# `EXAMPLES/skills-db/` — Skills exemples pour stack BDD (Alembic)

> Skill(s) stack-spécifique(s) BDD, à copier dans `.claude/skills/` et adapter.
> **Hors cœur du template** : l'outillage Alembic/SQLAlchemy n'est pas générique — il ne
> ship donc pas par défaut (comme les skills n8n, cf. [`../skills-n8n/`](../skills-n8n/README.md)).

| Skill                                  | Invocation      | Quoi                                                                             |
| -------------------------------------- | --------------- | -------------------------------------------------------------------------------- |
| [db-migration/](db-migration/SKILL.md) | `/db-migration` | Crée + teste une migration Alembic (upgrade/downgrade), ADR infra si structurant |

## Installation

Copié automatiquement par `/init-from-template` (type `bdd-migration`), ou à la main :

```bash
cp -r EXAMPLES/skills-db/db-migration .claude/skills/
```

**Le nom d'invocation = le nom du dossier** (`.claude/skills/db-migration/SKILL.md` → `/db-migration`).

## Pré-requis stack

- `alembic` + `sqlalchemy` installés, `alembic/` initialisé à la racine du projet.
- La permission `Bash(alembic:*)` est déjà dans `.claude/settings.json`.
