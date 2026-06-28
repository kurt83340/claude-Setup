# Glossaire — ACME / SAP B1

## Termes métier ACME

| Terme          | Définition                                                              |
| -------------- | ----------------------------------------------------------------------- |
| **Commande**   | Document de vente entre ACME et un client. Peut avoir plusieurs lignes. |
| **BL**         | Bon de Livraison — émis à l'expédition d'une commande                   |
| **Facture**    | Émise après livraison, peut couvrir 1 ou N commandes                    |
| **Client**     | Entité B2B (jamais B2C chez ACME). Identifié par `CardCode` SAP         |
| **Article**    | Produit vendu. Identifié par `ItemCode` SAP (= SKU)                     |
| **Commercial** | Membre de l'équipe vente ACME (3 personnes)                             |

## Termes SAP B1

| Terme             | Définition                                               |
| ----------------- | -------------------------------------------------------- |
| **Service Layer** | API REST officielle SAP B1 (depuis v9.x)                 |
| **DocEntry**      | ID interne unique d'un document SAP                      |
| **DocNum**        | Numéro affiché à l'utilisateur (séquentiel, par doctype) |
| **CardCode**      | Code client (string, ex: `C00125`)                       |
| **CardName**      | Nom du client (string)                                   |
| **DocTotal**      | Montant TTC du document                                  |
| **OINV**          | Table SAP des factures (Orders Invoice)                  |
| **ORDR**          | Table SAP des commandes                                  |
| **DocumentLines** | Lignes d'un document (array)                             |
| **UpdateDate**    | Date de dernière modification (pour le delta sync)       |

## Termes Notion

| Terme           | Définition                                   |
| --------------- | -------------------------------------------- |
| **Database**    | Table Notion (DB "Commandes" chez ACME)      |
| **Page**        | Ligne d'une DB (= 1 commande dans notre cas) |
| **Property**    | Colonne d'une DB                             |
| **Integration** | Bot Notion avec son token API                |
| **Relation**    | Lien entre 2 DBs (DB Commandes → DB Lignes)  |

## Termes projet

| Terme          | Définition                                                         |
| -------------- | ------------------------------------------------------------------ |
| **Sync delta** | Synchronisation seulement des nouveaux/modifiés depuis dernier run |
| **Upsert**     | Update si existe, insert sinon                                     |
| **Backfill**   | Sync initial pour rattraper l'historique                           |
| **Smoke test** | Test rapide post-déploiement pour vérifier que rien n'a pété       |

## Spécificités ACME à connaître

- Une "commande" SAP peut être facturée en plusieurs fois (acomptes)
- Le terme "client" recouvre 2 réalités : prospect (CRM externe) vs client actif (ERP)
- ACME utilise SAP B1 **on-premise** (pas Cloud)
- Pas d'EDI client → tout passe par SAP standard
