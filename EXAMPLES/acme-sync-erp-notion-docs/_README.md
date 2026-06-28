# ACME — Sync ERP→Notion

Sync automatique des commandes SAP Business One → Notion DB pour ACME Corp.

## Stack

- **n8n** (orchestration workflow)
- **Python 3.12** (helpers + transformations complexes)
- **SAP B1 Service Layer** (lecture commandes)
- **Notion API** (écriture DB Commandes)

## Setup local

```bash
# 1. Cloner et créer venv
git clone <repo>
cd acme-sync-erp-notion
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Variables d'env
cp .env.example .env
# Remplir avec les valeurs (voir .claude/docs/ACCESS.md pour les obtenir)

# 3. Tests
pytest

# 4. Lancer en local (une fois src/ créé)
python src/main.py --dry-run
```

## Déploiement

Voir [.claude/docs/RUNBOOK.md](.claude/docs/RUNBOOK.md).

## Documentation projet

Toute la doc projet est dans [.claude/docs/](.claude/docs/) :

- Brief + interlocuteurs : [.claude/docs/cadrage/README.md](.claude/docs/cadrage/README.md)
- Architecture : [.claude/docs/conception/ARCHITECTURE.md](.claude/docs/conception/ARCHITECTURE.md)
- Roadmap : [.claude/docs/ROADMAP.md](.claude/docs/ROADMAP.md)

## Contact

- Owner technique : Julien (technique.atlantis@gmail.com)
- Owner business ACME : Marie Dupont (marie@acme.fr)
