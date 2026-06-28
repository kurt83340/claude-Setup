# Diagramme — Flow métier ACME (synthèse cadrage)

> Diagramme de synthèse pour comprendre le **flow business existant** chez ACME
> et la **cible** post-projet. Sert à valider avec Marie qu'on a bien compris la demande.

## Flow actuel (avant projet)

```
┌──────────────┐    ┌────────────┐    ┌─────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────────┐
│  Commercial  │ ─► │  Saisie    │ ─► │   ERP   │ ─► │  Paul ⚠️    │ ─► │ Paul ⚠️ │ ─► │ Équipe vente │
│  passe cmd   │    │ SAP B1 (admin)│ │ enregistre│ │ exporte Excel│   │ colle Notion│ │  consulte    │
└──────────────┘    └────────────┘    └─────────┘    └──────────────┘    └──────────┘    └──────────────┘
                                                            ▲                  ▲
                                                            └─ 20-30 min/jour ─┘
                                                              latence 1 jour
```

**Problème :** étapes Paul = 20-30 min/jour, latence 1 jour pour Sophie.

## Flow cible (après projet v1.0)

```
┌──────────────┐    ┌────────────┐    ┌─────────┐                        ┌──────────────┐    ┌──────────────┐
│  Commercial  │ ─► │  Saisie    │ ─► │   ERP   │ ─── sync auto ──►     │  Notion DB   │ ─► │ Équipe vente │
│  passe cmd   │    │ SAP B1 (admin)│ │ enregistre│   < 15 min          │  Commandes   │   │  consulte    │
└──────────────┘    └────────────┘    └─────────┘                        └──────────────┘    └──────────────┘
                                          ✅                                    ✅
                                       (auto)                                (auto)
```

**Bénéfice :** plus de manip Paul, latence < 15 min, équipe vente plus réactive.

## Rôles dans le flow

| Persona                  | Avant                       | Après                       |
| ------------------------ | --------------------------- | --------------------------- |
| **Marie (CEO)**          | Demande des rapports à Paul | Consulte direct dans Notion |
| **Paul (IT)**            | 20-30 min/jour à exporter   | 0 manip, alerté si ça casse |
| **Sophie (commerciale)** | Attend exports manuels      | Vue temps réel dans Notion  |
| **Julien (moi)**         | N/A                         | Owner technique de la sync  |

## Validation

- ✅ Flow validé par Marie en kickoff (20/05)
- ✅ Architecture technique pour réaliser ça : [../../conception/ARCHITECTURE.md](../../conception/ARCHITECTURE.md)
