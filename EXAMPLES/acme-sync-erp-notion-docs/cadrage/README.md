# Cadrage — Sync ERP→Notion (ACME Corp)

> Ce dossier contient **tout ce qui sert à comprendre/définir le projet** + ses évolutions.
> Ce README est la **synthèse vivante** ; le détail brut est dans `tickets/`, `documents/`, `reunions/`.
>
> ⚠️ **Document vivant** : MAJ à chaque nouvelle réunion, ticket, pivot, accès accordé.
> Si pivot demandé par hiérarchie → réunion dans `reunions/YYYY-MM-DD-pivot.md` + MAJ ce README.

**Date kickoff :** 2026-05-20
**Demandeur :** Marie Dupont (CEO, ACME Corp)
**Canal initial :** Réunion kickoff 20/05 — voir [reunions/2026-05-20-kickoff.md](reunions/2026-05-20-kickoff.md)
**Tickets liés :** [JIRA-1234](tickets/JIRA-1234-export-clients.md), [JIRA-1235](tickets/JIRA-1235-sync-stock.md)
**Docs reçus :** voir [documents/](documents/)

## Interlocuteurs

| Nom          | Rôle             | Contact                      | Pour quoi                                          |
| ------------ | ---------------- | ---------------------------- | -------------------------------------------------- |
| Marie Dupont | CEO ACME         | marie@acme.fr                | Validation business, décisions scope, accès Notion |
| Paul Martin  | IT lead ACME     | paul@acme.fr                 | Accès techniques, ERP, VPN, n8n                    |
| Sophie L.    | Commerciale ACME | sophie@acme.fr               | UAT, retours utilisateur                           |
| Julien (moi) | Dev / Owner tech | technique.atlantis@gmail.com | Implémentation, livraison, support v1              |

**Décisionnaire final :** Marie (toute décision scope/archi/planning passe par elle).
**Cadence :** point hebdo vendredis 10h (Marie + Julien). Slack ACME : `#projet-sync-erp`.

> Pour les gros projets (> 5 stakeholders, plusieurs équipes), promouvoir dans un fichier `STAKEHOLDERS.md` dédié au niveau `docs/`.

## Demande exprimée (verbatim)

> "On a besoin que les nouvelles commandes de notre ERP remontent
> automatiquement dans Notion pour que l'équipe commerciale les voit
> sans avoir à se connecter à l'ERP. C'est urgent, on perd du temps
> chaque jour à faire des exports manuels."
>
> — Marie, kickoff 20/05

## Contexte

- **ERP :** SAP Business One 10.0 PL12 (on-premise, accessible via VPN)
- **API ERP :** Service Layer disponible (REST/JSON), doc fournie en [documents/](documents/)
- **Notion :** workspace ACME existant, DB "Commandes" déjà créée par Marie
- **Volume :** ~50 commandes/jour, pics à 200 en fin de mois
- **Fréquence souhaitée :** temps réel idéal, mais < 15 min acceptable

## Contraintes

- **Budget :** forfait défini (voir contrat), pas de coût SaaS récurrent au-delà
- **Sécurité :** credentials ERP en lecture seule UNIQUEMENT
- **Délai :** MVP fonctionnel pour 2026-06-15 (présentation board ACME)
- **Hébergement :** n8n on-premise ACME (pas n8n cloud — politique IT)

## Ce qui N'EST PAS demandé (out of scope)

- Sync bidirectionnel (lecture seule pour v1)
- Notifications Slack (peut-être v2)
- Modification du schéma Notion (DB déjà fixée par Marie)
- Multi-tenant (1 seule entité ACME pour l'instant)

## Risques identifiés au kickoff

- ERP SAP B1 = API parfois capricieuse (Paul IT a confirmé des soucis dans le passé)
- Notion API = rate limit 3 req/sec → batching à prévoir
- VPN ACME instable certains jours → retry/backoff obligatoire

## Suite

- ✅ Brief validé verbalement par Marie 20/05
- → PRD à écrire (`../conception/PRD.md`), validation Marie attendue avant 2026-05-28
- → ARCHITECTURE après validation PRD (`../conception/ARCHITECTURE.md`)

---

## Comment ce dossier est organisé

```
cadrage/
├── README.md         ← ce fichier (la synthèse vivante)
├── tickets/          ← tickets Jira/Linear/Asana reçus
├── documents/        ← docs client (PDF, Excel, captures)
├── reunions/         ← comptes-rendus de réunions (incl. pivots)
└── diagrams/         ← schémas business (ASCII + Excalidraw/SVG si gros)
```

**Le README synthétise** ; le reste contient le **matériel brut** pour traçabilité.

**Pour les diagrammes** : convention détaillée dans [diagrams/README.md](diagrams/README.md). En 2 mots : ASCII inline par défaut, Excalidraw + export SVG si gros.
