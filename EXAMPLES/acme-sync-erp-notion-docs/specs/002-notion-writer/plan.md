# Plan technique — 002 Notion Writer

## Architecture

```
src/notion_writer/
├── __init__.py
├── writer.py          # NotionWriter (point d'entrée)
├── mapping.py         # sap_order_to_notion_props()
├── exceptions.py      # NotionWriteError, NotionSchemaError
└── _http.py           # Wrapper notion-client + rate limit
```

## Classes

### `NotionWriter`

- `__init__(token: str, database_id: str)`
- `validate_schema() → None` (raise si schema KO)
- `upsert_order(order: Order) → str` (returns Notion page ID)
- `_find_by_doc_num(doc_num: str) → str | None`

## Stack

- `notion-client` (lib officielle Python)
- `tenacity` (retry sur 429)
- `pydantic` v2 (validation properties)

## Pattern rate limit

```python
class RateLimiter:
    def __init__(self, requests_per_sec: int = 3):
        self.min_interval = 1.0 / requests_per_sec
        self.last_request = 0

    def wait(self):
        elapsed = time.monotonic() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.monotonic()
```

## Mapping (extrait)

```python
def sap_order_to_notion_props(order: Order) -> dict:
    return {
        "Numéro commande": {"title": [{"text": {"content": order.doc_num}}]},
        "Client (code)": {"rich_text": [{"text": {"content": order.card_code}}]},
        "Client (nom)": {"rich_text": [{"text": {"content": order.card_name}}]},
        "Montant HT": {"number": float(order.doc_total)},
        "Date commande": {"date": {"start": order.doc_date.isoformat()}},
        "_DocEntry_SAP": {"number": order.doc_entry},  # hidden, pour traçabilité
    }
```

## Validation schema

Au démarrage : `client.databases.retrieve(database_id)` → check que toutes les properties attendues existent avec le bon type.

Si manquant → `NotionSchemaError` avec message clair pour Marie.

## Tests

- Mock notion-client avec `unittest.mock` (pas de lib respx équivalent)
- Test : create, update, schema validation, rate limit (sleep mock)

## Estimation

| Tâche                     | Estimation |
| ------------------------- | ---------- |
| Setup + rate limiter      | 2h         |
| Mapping fields            | 1h         |
| Upsert logic              | 3h         |
| Validation schema         | 2h         |
| Tests unitaires           | 3h         |
| Tests intégration staging | 2h         |
| **Total**                 | **~13h**   |
