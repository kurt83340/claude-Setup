# Plugin `db-migration`

> Skill de **migration de base de données (Alembic)**, packagé en **plugin Claude Code** installable par projet.
> Marketplace `claude-setup` (racine du repo : [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)).

| Skill | Invocation | Quoi |
| --- | --- | --- |
| [db-migration](skills/db-migration/SKILL.md) | `/db-migration:db-migration` | Génération, revue et application de migrations de schéma (Alembic) |

Skill auto-découvert par le harness (aucun listing `.claude/CLAUDE.md` requis).

## Installer (dans un projet)

```bash
/plugin marketplace add kurt83340/claude-Setup
claude plugin install db-migration@claude-setup --scope project
```

Désinstaller : `/plugin uninstall db-migration@claude-setup --scope project`.

> 🧩 Migrations = décisions structurantes → pense à un ADR (`/adr`) pour les choix de schéma non triviaux.
