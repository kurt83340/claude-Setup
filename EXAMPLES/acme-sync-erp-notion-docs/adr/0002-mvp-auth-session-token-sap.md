---
status: accepted
scope: mvp
phase: 2026-Q2
supersedes: null
---

# 0002 — Auth SAP B1 : session token rotatif

**Statut :** Accepted
**Date :** 2026-05-23
**Décideur :** Julien (validé Paul ACME IT)

## Contexte

SAP Business One Service Layer propose 2 méthodes d'authentification pour les appels API :

- **Session-based** : login → reçoit un cookie/token de session → expire après 30 min d'inactivité
- **Per-request basic auth** : envoyer login/password à chaque requête

Notre workflow tourne toutes les 10 min → la session sera quasi toujours active.

## Options considérées

### Option A — Basic auth à chaque appel

- Pro : simple, stateless
- Contre : SAP loggue chaque authentification (pollution logs), pas recommandé par SAP, lent (auth round-trip à chaque call)

### Option B — Session token, login à chaque run

- Pro : standard, propre
- Contre : login systématique inutile si session encore valide

### Option C — Session token avec refresh "lazy"

- Pro : login seulement si session expirée ou première fois
- Contre : un peu plus de code

## Décision

**Option C : session token avec refresh lazy**

Implémentation :

1. Au démarrage : tenter un appel API avec le token en cache (n8n Data Table)
2. Si 401 → login + cache nouveau token + retry
3. Sinon → utiliser le token cached

## Conséquences

- Moins d'appels d'auth (économie de quotas SAP)
- Logs SAP propres
- Pattern recommandé par la doc officielle SAP B1

* Code un peu plus complexe (gestion du cache)
* Si Data Table corrompue, on re-auth (pas dramatique)

## Notes sécurité

- Le token de session est stocké chiffré dans n8n Data Table
- Rotation manuelle du password compte API tous les 90 jours (procédure dans RUNBOOK)

## Liens

- ../specs/001-erp-connector/spec.md
- docs/conception/ARCHITECTURE.md (section Sécurité)
- Doc SAP B1 Service Layer : cadrage/documents/2026-05-21-doc-sap-service-layer.pdf
