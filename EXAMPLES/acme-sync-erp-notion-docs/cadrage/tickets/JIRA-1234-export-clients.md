# JIRA-1234 — Automatiser l'export des commandes vers Notion

**URL :** https://acme.atlassian.net/browse/JIRA-1234
**Créé par :** Marie Dupont
**Date :** 2026-05-18
**Priorité :** High
**Statut Jira :** In Progress (assigné à Julien externe)

## Description (verbatim)

> Aujourd'hui Paul me sort chaque matin un export Excel des nouvelles commandes
> de la veille pour que je puisse le coller dans notre DB Notion "Commandes".
> Ça prend 20-30 min/jour à Paul et je dois attendre qu'il ait le temps.
>
> Objectif : que les commandes apparaissent automatiquement dans Notion sans
> intervention humaine.

## Critères d'acceptation Jira

- [ ] Les nouvelles commandes apparaissent dans Notion DB "Commandes"
- [ ] Délai max : 15 min après création dans l'ERP
- [ ] Pas de doublon (si commande déjà sync, juste update)
- [ ] Logs / alertes si ça plante

## Pièces jointes Jira

- `export-exemple-2026-05-15.xlsx` → archivé dans [../documents/](../documents/)
- `screenshot-notion-db.png` → archivé dans [../documents/](../documents/)

## Notes Julien

- C'est le ticket principal qui déclenche le projet
- À croiser avec [JIRA-1235](JIRA-1235-sync-stock.md) (demande connexe mais hors scope v1)
- Validation finale par Marie, pas par Jira (Marie ne suit pas Jira)
