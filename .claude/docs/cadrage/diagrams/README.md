# diagrams/ — Schémas de synthèse business (cadrage)

Diagrammes pour **comprendre/visualiser le cadrage** : flow métier client, processus existant vs cible, organigramme, mindmap des concepts métier.

## Convention diagrammes (3 formats supportés)

### 1. ASCII inline (DEFAULT — le plus Claude-friendly)

Pour diagrammes simples (flow linéaire, arbres). Mets-les directement dans `cadrage/README.md` ou dans un `.md` ici. Exemple : [`flow-business-{{nom}}.md`](flow-business-{{nom}}.md).

### 2. Excalidraw / PNG / SVG (pour diagrammes complexes)

**Règle d'or :** commit **la source ET l'export** côte à côte.

```
diagrams/
├── flow-X.excalidraw    # source éditable (Excalidraw)
├── flow-X.svg           # export pour Claude + GitHub preview
├── mindmap-Y.png        # MindMap exportée
└── ...
```

→ Toi humain édites le `.excalidraw`, tu exportes en `.svg` à chaque modif majeure.
→ Claude lit le SVG via Read explicite (le `.excalidraw` JSON aussi mais comprend mal visuellement).

### 3. Mermaid inline (si tu changes d'avis)

Pas utilisé actuellement (décision utilisateur : ASCII préféré). Mais possible si besoin.

## Référencer un diagramme depuis un autre document

```markdown
Voir [flow business](diagrams/flow-business-{{nom}}.md)
ou
![Flow business](diagrams/flow-business-{{nom}}.svg)
```

⚠️ Claude ne suit pas automatiquement `![](path)` quand il lit un .md — il faut un Read explicite ou pointer vers un .md qui contient l'ASCII.

## Gitignore

- ✅ Versionner les `.excalidraw` (source = doc projet)
- ✅ Versionner les exports `.svg`, `.png`
- ❌ Gitignore : `*.excalidraw.bak`, exports temporaires
