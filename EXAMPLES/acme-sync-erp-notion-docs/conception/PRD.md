# PRD — Sync ERP→Notion v1.0

> 🎯 **Pour qui** : Marie (CEO ACME), Sophie (commerciale), validateurs business
> 📋 **Ce fichier dit** : le **QUOI** + **POURQUOI** (vision, scope, personas, user stories, métriques, validations)
> ❌ **Ne contient PAS** : stack technique, modules, flux d'implémentation → voir [ARCHITECTURE.md](ARCHITECTURE.md)

**Statut :** Approved (Marie, 2026-05-27)
**Version :** 1.0
**Dernière MAJ :** 2026-05-27
**Source :** [../cadrage/README.md](../cadrage/README.md) + [../cadrage/reunions/2026-05-26-validation-prd.md](../cadrage/reunions/2026-05-26-validation-prd.md)
**Research / brainstorm :** [research.md](research.md)

## 1. Vision

Permettre à l'équipe commerciale ACME de consulter les commandes ERP **en quasi temps réel** dans Notion, sans accès direct au SAP B1.

## 2. Problème résolu

Aujourd'hui : l'équipe commerciale demande des exports manuels à l'IT (~30 min/jour de Paul). Latence info : 1-2 jours.

Après : info disponible dans Notion en <15 min, sans intervention IT.

## 3. Personas

| Persona                  | Besoin                               | Use case principal                                    |
| ------------------------ | ------------------------------------ | ----------------------------------------------------- |
| **Commerciale** (Sophie) | Voir les nouvelles commandes du jour | Consultation Notion DB "Commandes" matin + après-midi |
| **CEO** (Marie)          | Reporting hebdo sans manipuler l'ERP | Vue Notion filtrée par semaine                        |
| **IT** (Paul)            | Ne plus faire les exports manuels    | N'utilise plus le système (release du temps)          |

## 4. Scope v1.0

### IN

- Sync **unidirectionnel** ERP → Notion
- Entités synchronisées : **Commandes** (entête + lignes)
- Fréquence : **toutes les 10 minutes**
- Filtre : commandes créées/modifiées dans les 24h
- Mapping champs ERP → Notion (cf. [ARCHITECTURE.md](ARCHITECTURE.md))
- Détection delta (pas de full re-sync à chaque run)
- Logs + alerting email si > 3 erreurs consécutives

### OUT (v2+)

- Sync inverse (Notion → ERP)
- Autres entités (clients, articles, factures)
- Notifications Slack
- Dashboard de monitoring custom (n8n native suffit pour v1)

## 5. User stories

- **US1** En tant que commerciale, je veux voir les nouvelles commandes de la journée dans Notion → CDA : commande apparue dans Notion < 15 min après création ERP
- **US2** En tant que CEO, je veux que ça tourne tout seul → CDA : 0 intervention humaine pendant 7 jours consécutifs
- **US3** En tant qu'IT, je veux être alerté si ça casse → CDA : email à Paul + Julien si > 3 erreurs consécutives en 1h

## 6. Métriques de succès

- **Latence p95** : < 15 min entre création ERP et apparition Notion
- **Disponibilité** : > 99% sur 30 jours (max 7h downtime/mois)
- **Adoption** : Sophie utilise Notion 5j/7 (vs anciens exports) après 1 mois

## 7. Hypothèses & risques

| Hypothèse                       | Risque si faux  | Mitigation                           |
| ------------------------------- | --------------- | ------------------------------------ |
| API SAP B1 stable en production | Tout casse      | Retry exponentiel + alerting         |
| Notion DB schema ne change pas  | Mapping cassé   | Test schema au démarrage du workflow |
| VPN ACME up 99% du temps        | Manque de syncs | Retry + alerting + buffer 1h         |

## 8. Validation

- ✅ Brief Marie : 2026-05-20
- ✅ PRD Marie : 2026-05-27 (mail de validation archivé)
- ⏳ Validation tech Paul IT : prévue 2026-05-29
- ⏳ Validation finale Marie pour mise en prod : avant 2026-06-15
