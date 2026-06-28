# Code Map — Intention & contraintes (Sync ERP→Notion)

> **Ce que Claude NE PEUT PAS deviner en lisant le code.** Le rôle d'un fichier, ses
> imports et ses tests se retrouvent en `grep`/lecture (agentic search) — on ne les
> documente donc pas ici. On garde le non-déductible : vue macro, règles de couplage,
> intention, gotchas.
>
> ⚠️ Avant d'éditer un fichier, vérifie les **règles de couplage** ci-dessous.

**Dernière MAJ :** 2026-05-20

## Vue d'ensemble (macro)

```
sap_connector  ──►  main (orchestrateur)  ──►  notion_writer
   (lecture SAP B1)        │                       (écriture Notion)
                           └──►  error_handler  (classifie + notifie)
```

→ Pour toucher la lecture SAP → `src/sap_connector/`. L'écriture Notion → `src/notion_writer/`.
La gestion d'erreurs transverse → `src/error_handler/`. Le détail des fichiers se lit dans le code.

## Règles de couplage (⭐ non déductible)

- ❌ `sap_connector` ne doit **JAMAIS** importer `notion_writer` (ni l'inverse) — les deux connecteurs sont étanches
- ❌ `sap_connector` et `notion_writer` ne doivent **JAMAIS** importer `error_handler`
- ✅ Seul `main.py` connaît les 3 modules ensemble (orchestration)
- ✅ `error_handler.classifier` connaît les **exceptions** de `sap_connector` et `notion_writer` (pour les classifier) mais PAS leurs implémentations

## Intention & décisions locales

- Les 2 connecteurs sont étanches pour pouvoir **remplacer Notion par un autre back** en v2 sans toucher la lecture SAP
- Toute requête sortante passe par un `_http` de module (`sap_connector/_http.py`, `notion_writer/_http.py`) — retry + rate-limit **centralisés** là, jamais dans le code métier
- `notion_writer/mapping.py` = pure functions (SAP `Order` → props Notion), testables sans I/O — ne jamais y mettre d'appel réseau
- Montants : centimes `int` partout, jamais `float`

## Gotchas

- ⚠️ L'API Notion renvoie parfois `200` avec une erreur dans le body → `notion_writer/_http.py` vérifie le body, pas seulement le status
- ⚠️ `error_handler.notifier` a un cooldown (`state.track_recent_errors`) : en cas de boucle d'erreurs, toutes les alertes ne partent pas — c'est voulu (anti-spam), ne pas « corriger »
- ⚠️ SAP B1 rate-limite à ~100 req/min → la pagination dans `sap_connector/client.py` respecte un délai ; ne pas paralléliser sans revoir ça

## Quand mettre à jour ce fichier

- Nouvelle règle de couplage / contrainte d'archi → l'ajouter
- Nouveau gotcha qui t'a coûté du temps → le noter (avec pointer `fichier:ligne`)
- Découpage en sous-systèmes modifié → revoir la vue macro
- ❌ PAS de description fichier-par-fichier ni de liste d'imports (déductible + drift)

> 🔁 `/codemap` régénère la vue macro + détecte les violations de couplage. Le hook
> `pretooluse-inject-codemap.py` réinjecte couplage + intention + gotchas avant édition.
