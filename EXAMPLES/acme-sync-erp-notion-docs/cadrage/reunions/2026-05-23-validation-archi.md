# Validation architecture — Paul (ACME IT)

**Date :** 2026-05-23 16h-16h45
**Présents :** Paul Martin (ACME IT), Julien
**Format :** Visio Google Meet
**Support :** [docs/conception/ARCHITECTURE.md](../../ARCHITECTURE.md) (présentée en partage écran)

## Sujets abordés

### 1. Stack proposée

- n8n on-premise + Python helpers → ✅ validé Paul
- Stockage delta dans n8n Data Tables → ✅ validé (pas de BDD séparée pour v1)

### 2. Sécurité

- Credentials dans n8n credentials (AES-256) → ✅ validé
- Lecture seule sur SAP via compte dédié → ✅ Paul a créé le compte
- VPN obligatoire pour atteindre l'ERP → ✅ noté

### 3. Observabilité

- Sentry sur mon compte perso pour le MVP → ⚠️ Paul OK pour MVP mais à migrer sur compte ACME en v1.1
- Email alerting via SMTP ACME → ⏳ Paul ouvre ticket IT pour fournir SMTP

### 4. Volumétrie

- 50 commandes/jour, pics 200 fin de mois → ✅ pas un souci pour le pattern proposé
- Retention executions n8n : 30 jours → ✅ suffisant

## Décisions prises

- ✅ ADR-0001 (stack) validé
- ✅ ADR-0002 (auth ERP) validé
- ✅ ADR-0003 (Data Tables) validé
- ⚠️ Action ouverte : migration Sentry → compte ACME (v1.1)

## Préoccupations Paul

- "L'API SAP B1 peut être instable les lundis matin (batch nuit ACME)"
  → Mitigation : retry exponentiel + alerting si > 3 erreurs/h
- "Le VPN tombe parfois sans prévenir"
  → Mitigation : retry + buffer Data Tables (re-tente au prochain run)

## Actions

- [ ] Paul : ouvrir ticket pour SMTP ACME (avant 2026-05-25)
- [x] Julien : ajouter ADR-0001/0002/0003 dans le repo ✅ fait
- [ ] Julien : valider l'archi avec Marie aussi (next réunion 2026-05-27)
