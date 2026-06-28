# Runbook — Sync ERP→Notion

> ⚠️ **À CRÉER QUAND :** premier déploiement en prod (pas avant).
> Tant que le projet est en dev/MVP, ce fichier est inutile.
> Le créer quand quelque chose tourne en continu et peut casser sans toi.

**Dernière MAJ :** 2026-05-24
**Owner astreinte :** Julien (premier niveau), Paul (escalade infra)

## Déploiement

### Pré-requis

- Branche `main` à jour, CI verte
- Backup BDD Notion fait (export manuel via Notion UI)
- Fenêtre de déploiement : éviter 8h-10h (pic commandes ACME)

### Procédure standard

```bash
# 1. Vérifs
git checkout main && git pull
pytest

# 2. Push workflow n8n
/n8n-push  # ou : python scripts/deploy.py --target n8n-prod

# 3. Vérifier en n8n UI que le workflow est bien Active
# 4. Lancer un run manuel pour smoke test
# 5. Vérifier dans Notion qu'au moins 1 commande est apparue

# 6. Tag git
git tag -a v2026.05.24-1430 -m "Deploy MVP"
git push --tags

# 7. Update doc
# - docs/CHANGELOG.md : entrée de déploiement
# - docs/HANDOFF.md : status "déployé"
```

### Rollback workflow n8n

```bash
# 1. Identifier la version précédente (tag git)
git log --oneline --tags

# 2. Checkout du JSON précédent
git show v2026.05.20-1000:workflows/sync-erp.json > /tmp/previous.json

# 3. Import dans n8n (UI ou API)
# Attention : credentials ne sont pas réimportés, vérifier qu'ils sont OK
```

## Monitoring

- **n8n executions** : tenant ACME > workflow "Sync ERP" > Executions
- **Sentry** : sentry.io/acme-sync-erp
- **Alertes** : email à Paul + Julien si > 3 erreurs consécutives en 1h

## Si ça casse — Playbook

### Symptôme : pas de nouvelles commandes dans Notion depuis > 30 min

1. Check n8n executions : y a-t-il eu des runs récents ?
   - **NON** → check trigger Schedule (peut-être désactivé)
   - **OUI mais en erreur** → voir le code erreur ci-dessous

2. Erreur **401 ERP** → token SAP expiré
   - Lancer la procédure "Refresh token ERP" (ci-dessous)

3. Erreur **429 Notion** → rate limit
   - Augmenter l'intervalle dans Schedule node (10min → 15min)
   - Vérifier qu'on bat pas un autre workflow Notion en parallèle

4. Erreur **5xx Notion** → problème côté Notion
   - Check status.notion.com
   - Le retry auto (3x) devrait gérer → attendre 30 min

5. Erreur **VPN down** → check avec Paul si VPN ACME opérationnel

### Refresh token ERP

```bash
# 1. SSH sur le bastion ACME
ssh acme-bastion

# 2. Régénérer le token
cd /opt/sap-tools && ./refresh-token.sh acme_api_sync

# 3. Copier le token affiché
# 4. Dans n8n UI : Credentials > "SAP B1 Token" > Edit > Update token
```

### Incident grave (> 2h sans sync)

1. Désactiver le workflow n8n (évite spam d'erreurs)
2. Notifier Marie + Paul sur Slack `#projet-sync-erp`
3. Investiguer (logs n8n + Sentry)
4. Fixer ou rollback
5. Réactiver workflow + lancer run manuel
6. Post-mortem si > 4h : créer un ADR avec leçons apprises

## Maintenance préventive

- **Hebdo** : check Sentry pour erreurs récurrentes non bloquantes
- **Mensuel** : rotation token API SAP (procédure ci-dessus)
- **Trimestriel** : revue des credentials (qui a accès ? toujours nécessaire ?)

## Contacts urgence

| Heure        | Premier contact | Escalade            |
| ------------ | --------------- | ------------------- |
| 9h-18h L-V   | Julien (Slack)  | Marie (mail)        |
| Soir/weekend | Julien (mail)   | Pas d'astreinte SLA |
