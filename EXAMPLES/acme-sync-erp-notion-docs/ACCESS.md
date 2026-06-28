# Accès requis — Sync ERP→Notion

**Dernière MAJ :** 2026-05-22

## ✅ Obtenus

- [x] **SAP B1 Service Layer** : compte API readonly `acme_api_sync` — reçu 2026-05-21 (Paul)
- [x] **Notion** : integration token "sync-erp-bot" — créé par Marie 2026-05-22
- [x] **VPN ACME** : compte `julien.ext` — actif depuis 2026-05-21 (ticket IT #4520)
- [x] **n8n on-premise** : compte admin sur tenant ACME — reçu 2026-05-23 (Paul)
- [x] **Sentry** : projet "acme-sync-erp" créé sur mon compte personnel

## ⏳ En attente

- [ ] **Accès écriture Notion DB "Commandes"** : Marie doit partager la DB avec l'integration (relancée 2026-05-23)
- [ ] **Compte SMTP ACME** pour les alertes email : ticket IT #4527 ouvert

## 🔒 Stockage des credentials

- **1Password vault "ACME"** : tous les credentials maître (partagé avec Marie)
- **`.env` local** : copier depuis `.env.example`, valeurs à récupérer dans 1Password
- **n8n credentials** : stockés dans n8n directement (chiffrés AES-256 par n8n)
- **Sentry DSN** : dans `.env` (pas sensible mais quand même pas dans le repo)

❌ **JAMAIS de credentials dans le repo Git** (gitleaks en pre-commit)

## Contacts pour les accès

| Besoin               | Contact | Délai habituel         |
| -------------------- | ------- | ---------------------- |
| Notion / business    | Marie   | < 24h                  |
| ERP / IT / VPN / n8n | Paul    | 2-3 jours (tickets IT) |
| Compte ACME divers   | Paul    | 1 semaine              |

## Procédure de revocation (fin de mission)

1. Marie révoque l'integration Notion
2. Paul désactive le compte API SAP `acme_api_sync`
3. Paul supprime le compte VPN `julien.ext`
4. Paul supprime le compte n8n admin
5. Je supprime mon coffre 1Password "ACME"
6. Je supprime mon `.env` local et le repo
