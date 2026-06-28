# diagrams/ — Schémas techniques (conception)

> Placeholder pour les **diagrammes techniques complexes** (composants, séquences, data flow) qui méritent un fichier séparé.

## Convention

**Par défaut, les diagrammes techniques vivent INLINE dans `ARCHITECTURE.md`** (ASCII art). Voir [`../ARCHITECTURE.md`](../ARCHITECTURE.md) section 1.

**Utilise ce dossier UNIQUEMENT si :**

- Diagramme trop gros pour rester inline (> 50 lignes ASCII)
- Tu veux une version éditable (Excalidraw)
- Tu veux un export SVG/PNG pour partage externe (présentation client, doc Notion)

## Formats supportés (même règle que cadrage/diagrams/)

| Format                              | Usage                        | Claude-friendly ?         |
| ----------------------------------- | ---------------------------- | ------------------------- |
| ASCII inline (dans ARCHITECTURE.md) | Par défaut                   | ✅ Parfait                |
| `.md` séparé (ASCII)                | Si gros diagramme texte      | ✅ Parfait                |
| `.excalidraw` + `.svg` export       | Diagrammes visuels complexes | ⚠️ SVG via Read explicite |
| PNG                                 | Screenshots, photos          | ⚠️ Pas fiable mai 2026    |

## Convention de commit

```
conception/diagrams/
├── archi-detaillee.excalidraw   # source éditable
└── archi-detaillee.svg          # export pour Claude + GitHub
```

## Référencer depuis ARCHITECTURE.md

```markdown
Vue d'ensemble : voir ci-dessus (ASCII inline).
Schéma détaillé : [diagrams/archi-detaillee.md](diagrams/archi-detaillee.md)
ou [diagrams/archi-detaillee.svg](diagrams/archi-detaillee.svg)
```

## Specs/ (micro)

Pour les diagrammes spécifiques à UNE feature → mets-les **inline dans le `plan.md`** de la spec. Crée `specs/00X-feature/diagrams/` seulement si nécessaire (rare).
