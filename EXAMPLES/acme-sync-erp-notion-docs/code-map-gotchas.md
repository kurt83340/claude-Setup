# Gotchas — pièges non évidents (injectés à la demande)

> Non auto-chargé : le hook PreToolUse injecte les entrées qui citent le fichier édité (backticks).

## Globaux

## Par zone

- ⚠️ L'API Notion renvoie parfois `200` avec une erreur dans le body → `notion_writer/_http.py` vérifie le body, pas seulement le status
- ⚠️ `error_handler.notifier` a un cooldown (`state.track_recent_errors`) : en cas de boucle d'erreurs, toutes les alertes ne partent pas — c'est voulu (anti-spam), ne pas « corriger »
- ⚠️ SAP B1 rate-limite à ~100 req/min → la pagination dans `sap_connector/client.py` respecte un délai ; ne pas paralléliser sans revoir ça
