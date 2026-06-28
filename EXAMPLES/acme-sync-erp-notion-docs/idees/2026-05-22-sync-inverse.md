# Idée — Sync inverse Notion → ERP

**Date :** 2026-05-22
**Source :** Discussion informelle avec Marie en fin de kickoff

## Pitch

Permettre à l'équipe commerciale de **créer une commande** directement depuis Notion (form), avec push automatique vers SAP B1.

## Use case

Sophie reçoit un appel client → veut enregistrer la commande immédiatement → aujourd'hui doit ouvrir SAP (lent, pas user-friendly) → demain remplit un form Notion → 5 min plus tard la commande est dans SAP.

## Pourquoi pas en v1

- Marie a explicitement dit "pas en v1, on commence par lecture seule"
- Risque sécurité : écrire dans l'ERP demande une validation supplémentaire (RGPD, audit)
- Plus complexe : validation, rollback, gestion conflits

## À considérer pour v2

- Sécurité : compte API SAP en écriture séparé du compte lecture
- Form Notion → webhook n8n → validation → SAP API POST
- Cas d'usage à creuser : juste création ou aussi update ?
- UAT obligatoire avec Sophie avant prod

## Estimation grossière

- 2-3 semaines de dev (vs 4 semaines pour la v1)
- Refacto nécessaire du workflow n8n actuel

## Statut

💡 **Idée backlog v2** — à ré-évaluer après mise en prod v1.0
