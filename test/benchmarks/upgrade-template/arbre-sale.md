---
name: arbre-sale
skill: upgrade-template
input: /upgrade-template
state: projet généré en v1.4.1 avec un fichier modifié non commité (src/app.py)
assert-contains:
  - "git"
assert-not-contains:
  - "template-lock.json"
---

## Attendu

- Le skill **refuse de continuer** tant que l'arbre git n'est pas propre et propose de committer
  ou stasher d'abord (le diff de mise à jour doit se relire seul)
- **Aucun fichier** du projet n'est modifié (ni lock, ni settings, ni hooks)
- Pas de contournement silencieux par `--allow-dirty`
