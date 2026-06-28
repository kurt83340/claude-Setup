# Idée — Alertes Slack sur grosses commandes

**Date :** 2026-05-23
**Source :** Idée perso en codant le SAP connector

## Pitch

Quand une commande > 10k€ est sync depuis l'ERP, envoyer une notification Slack dans `#ventes-acme` pour que l'équipe commerciale soit alertée immédiatement.

## Use case

Aujourd'hui : commande importante posée → personne au courant avant le lendemain matin. Souvent ça nécessite un follow-up rapide (relation client VIP).

Demain : notif Slack immédiate avec lien vers la page Notion → réactivité 10x meilleure.

## Effort estimé

- Très faible : ajout d'un node IF + Slack dans le workflow n8n existant
- 30 min de dev + tests

## Pourquoi pas tout de suite

- Pas dans le scope v1 validé avec Marie
- Mais petit ajout post-MVP très ROI

## À discuter

- Seuil : 10k€ ? Configurable ?
- Canal Slack : `#ventes-acme` (à confirmer existence)
- Mentions : @-tag d'un commercial spécifique ? (mapping CardCode → personne)
- Anti-spam : pas de notif si on relance le sync sur du backfill

## Statut

💡 **Idée intéressante pour v1.1** — à proposer à Marie après mise en prod v1.0
