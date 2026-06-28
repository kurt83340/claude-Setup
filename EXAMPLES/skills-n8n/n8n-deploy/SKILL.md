---
name: n8n-deploy
description: {{Déploie en prod (procédure complète, à adapter)}}
disable-model-invocation: true
---

> 💡 **Skill exemple à adapter**. Supprime/renomme selon ton projet.
> `disable-model-invocation: true` = uniquement via `/n8n-deploy` (un deploy ne doit JAMAIS se déclencher tout seul).

Procédure de déploiement complète.

⚠️ **À VALIDER avec moi avant chaque étape destructive.**

Étapes :

1. Vérifier qu'on est sur `main` et à jour (`git status`)
2. Lancer les tests ({{commande_tests}})
3. **DEMANDER CONFIRMATION** avant de continuer
4. {{Backup BDD prod si applicable}}
5. {{Appliquer migrations BDD si applicable}}
6. {{Push workflow / artifacts}}
7. Smoke test post-deploy ({{commande}})
8. Update `.claude/docs/CHANGELOG.md` avec la version déployée + date + tag git
9. Update `.claude/docs/HANDOFF.md` (status "déployé en prod")

En cas d'erreur, voir [.claude/docs/RUNBOOK.md](../../docs/RUNBOOK.md) section Rollback.
