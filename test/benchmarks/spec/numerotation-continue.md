---
name: numerotation-continue
skill: spec
input: /spec "Export CSV" alors que specs/001-… et specs/002-… existent déjà (002 livrée [x])
state: deux specs existantes 001 et 002 dans specs/ + lignes ROADMAP correspondantes ([x] pour 002)
assert-contains:
  - "003-export-csv"
  - "status: draft"
assert-not-contains:
  - "001-export-csv"
  - "{{SPEC_"
---

## Attendu

- Numéro alloué = **max + 1** (`003`) — jamais de reset, même si la dernière spec est livrée
- 4 fichiers créés depuis les templates bundlés, placeholders `{{SPEC_*}}` tous substitués
- `spec.md` créé avec frontmatter `status: draft` (source machine-readable de l'état)
- `tasks.md` créé avec la grammaire DoD typée (`command_passes:` / `file_exists:` / `manual:`)
- Ligne ROADMAP ajoutée en `[ ]` (ou `[~]` + frontmatter `in-progress` si démarrage immédiat
  accepté) — jamais de spec sans ligne ROADMAP
- Titre + phase demandés via AskUserQuestion AVANT toute écriture
