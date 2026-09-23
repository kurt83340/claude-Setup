---
name: conflit-garde
skill: upgrade-template
input: /upgrade-template (chemin du dépôt template local en argument)
state: projet généré en v1.4.1 (python-app), arbre git propre ; l'utilisateur a personnalisé la rule git-workflow (ligne ajoutée au milieu) ET réécrit un titre de rules/template-maintenance.md ; il a supprimé le skill pivot
assert-contains:
  - "dry-run"
  - "conflit"
  - ".claude/.cache/upgrade-"
assert-not-contains:
  - "Traceback"
---

## Attendu

- Le **dry-run est montré AVANT** toute écriture (versions de → vers, profil déduit à confirmer,
  mises à jour / fusions / conflits / migrations), puis validation demandée
- `rules/git-workflow.md` : **fusion 3 voies** appliquée (ligne maison conservée + correctif gitleaks amont)
- `rules/template-maintenance.md` : **conflit** — le fichier du projet n'est PAS modifié ; la version
  cible est déposée dans `.claude/.cache/upgrade-<v>/` et une fusion est proposée à l'utilisateur
- Le skill `pivot` supprimé par l'utilisateur **n'est pas réintroduit**
- Fin : commit sur chemins explicites (`git add .claude/ CLAUDE.md …`), rappel de relancer Claude Code
