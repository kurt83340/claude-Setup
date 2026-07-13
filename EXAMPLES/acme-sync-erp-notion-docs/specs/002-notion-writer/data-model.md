# Data model — Notion DB "Commandes"

## Schéma cible (Marie a créé la DB)

| Property name    | Type   | Source SAP   | Notes                   |
| ---------------- | ------ | ------------ | ----------------------- |
| Numéro commande  | Title  | `DocNum`     | Clé business affichée   |
| Client (code)    | Text   | `CardCode`   |                         |
| Client (nom)     | Text   | `CardName`   |                         |
| Montant HT       | Number | `DocTotal`   | Format devise EUR       |
| Date commande    | Date   | `DocDate`    | ISO 8601                |
| Dernière MAJ ERP | Date   | `UpdateDate` | datetime                |
| Statut sync      | Select | (calculé)    | "Sync OK" / "Erreur"    |
| \_DocEntry_SAP   | Number | `DocEntry`   | Caché, pour traçabilité |
| \_Synced at      | Date   | (calculé)    | datetime du sync        |

## Properties à vérifier au démarrage

`NotionWriter.validate_schema()` doit checker que toutes ces properties existent avec le bon type. Si manquant → `NotionSchemaError`.

## Clé unique

`_DocEntry_SAP` (number) — clé business stable côté SAP, ne change jamais.

Pour la recherche idempotente :

```python
client.databases.query(
    database_id=DB_ID,
    filter={"property": "_DocEntry_SAP", "number": {"equals": doc_entry}}
)
```

## Évolutions prévues (v2)

- Relation `Lignes` → DB "Lignes commandes" (sub-pages par ligne)
- Relation `Commercial` → DB "Équipe" (CardCode → personne)
- Rollup `Total CA client` → cumul par client
