# Runbook — {{PROJECT_NAME}}

> ⚠️ **À CRÉER QUAND :** premier déploiement en prod (pas avant).
> Tant que le projet est en dev/MVP, ce fichier est inutile.
> Le créer quand quelque chose tourne en continu et peut casser sans toi.

**Dernière MAJ :** {{YYYY-MM-DD}}
**Owner astreinte :** {{Toi}} (premier niveau), {{Owner IT client}} (escalade infra)

## Déploiement

### Pré-requis

- Branche `main` à jour, CI verte
- Backup {{si applicable}} fait
- Fenêtre de déploiement : éviter {{créneaux à risque}}

### Procédure standard

```bash
# 1. Vérifs
git checkout main && git pull
{{COMMANDE_TESTS}}

# 2. Push / déploy
{{/deploy ou commande spécifique}}

# 3. Smoke test post-deploy
{{vérification visuelle / API ping / etc.}}

# 4. Tag git
git tag -a v$(date +%Y.%m.%d-%H%M) -m "Deploy {{description}}"
git push --tags

# 5. Update doc
# - docs/CHANGELOG.md : entrée de déploiement
# - docs/HANDOFF.md : status "déployé"
```

### Rollback

```bash
# 1. Identifier la version précédente (tag git)
git log --oneline --tags

# 2. {{Procédure rollback spécifique}}
{{instructions...}}
```

## Monitoring

- **{{Monitoring 1}}** : {{URL / accès}}
- **{{Sentry / autre}}** : {{URL}}
- **Alertes** : {{configuration alerting}}

## Si ça casse — Playbook

### Symptôme : {{Symptôme 1}}

1. Check {{où regarder}}
2. Si {{erreur A}} → {{procédure}}
3. Si {{erreur B}} → {{procédure}}

### {{Procédure de fix courante 1}}

```bash
# Étapes détaillées
```

### Incident grave ({{seuil}})

1. {{Action 1 : désactiver, notifier}}
2. {{Action 2 : investiguer}}
3. {{Action 3 : fixer ou rollback}}
4. Post-mortem → créer un ADR avec leçons apprises

## Maintenance préventive

- **Hebdo** : {{check à faire chaque semaine}}
- **Mensuel** : {{rotation tokens / autre}}
- **Trimestriel** : {{revue accès / autre}}

## Contacts urgence

| Heure        | Premier contact | Escalade                  |
| ------------ | --------------- | ------------------------- |
| 9h-18h L-V   | {{Toi (Slack)}} | {{Décideur (mail)}}       |
| Soir/weekend | {{Toi (mail)}}  | {{Pas d'astreinte / SLA}} |
