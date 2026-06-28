# diagrams/ — Schémas techniques (conception)

Diagrammes techniques **complexes** (composants, séquences, data flow) qui méritent un fichier séparé.

**Par défaut → ASCII inline** dans [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §1. Crée un fichier séparé ici (`.md` ASCII, ou `.excalidraw` + export `.svg` côte à côte) uniquement si > ~50 lignes ASCII ou besoin d'un visuel éditable/partageable.

> 📐 **Convention complète** (3 formats, règle « source éditable + export côte à côte », gitignore, limites Claude sur `![](path)`) → **[template-maintenance.md § Convention diagrammes](../../../rules/template-maintenance.md#convention-diagrammes-3-formats)** _(source unique — ne pas recopier ici pour éviter le drift)_.

Diagramme spécifique à **une feature** → inline dans le `plan.md` de la spec (créer `specs/00X/diagrams/` seulement si nécessaire, rare).
