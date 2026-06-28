# Accès requis — {{PROJECT_NAME}}

**Dernière MAJ :** {{YYYY-MM-DD}}

## ✅ Obtenus

- [ ] **{{Service/Système 1}}** : {{type d'accès}} — reçu {{YYYY-MM-DD}} ({{personne}})
- [ ] **{{Service 2}}** : ... — ...
- [ ] ...

## ⏳ En attente

- [ ] **{{Accès en cours}}** : {{description}} ({{personne en charge}}, ticket {{#XXXX}})
- [ ] ...

## 🔒 Stockage des credentials

- **{{Vault / 1Password / Doppler}}** : tous les credentials maître
- **`.env` local** : copier depuis `.env.example`, valeurs à récupérer dans {{vault}}
- **{{n8n credentials / autre service de stockage}}** : stockés chiffrés
- **{{Sentry DSN / autres clés non-sensibles}}** : dans `.env` (pas dans le repo)

❌ **JAMAIS de credentials dans le repo Git** (gitleaks en pre-commit recommandé)

## Contacts pour les accès

| Besoin                               | Contact | Délai habituel |
| ------------------------------------ | ------- | -------------- |
| {{Catégorie 1}} ({{ex: business}})   | {{Nom}} | < 24h          |
| {{Catégorie 2}} ({{ex: IT / infra}}) | {{Nom}} | 2-3 jours      |
| {{Catégorie 3}}                      | {{Nom}} | 1 semaine      |

## Procédure de revocation (fin de mission)

1. {{Étape 1 — qui révoque quoi}}
2. {{Étape 2}}
3. {{Étape 3}}
4. Suppression `.env` local + clone du repo
