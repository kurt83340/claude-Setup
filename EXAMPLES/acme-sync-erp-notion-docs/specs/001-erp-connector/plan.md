# Plan technique — 001 ERP Connector

## Architecture du module

```
src/sap_connector/
├── __init__.py
├── client.py          # SapClient (point d'entrée public)
├── auth.py            # AuthManager (login, refresh, cache token)
├── models.py          # Order, OrderLine (Pydantic models)
├── exceptions.py      # SapApiError, SapAuthError, SapTimeoutError
└── _http.py           # Wrapper httpx (retry, timeout, headers)
```

## Classes principales

### `SapClient`

Point d'entrée public. Méthodes :

- `__init__(base_url, company_db, username, password, http_client=None)`
- `get_orders_since(timestamp: datetime) → list[Order]`
- `get_order_lines(doc_entry: int) → list[OrderLine]`
- `health_check() → bool`

### `AuthManager`

- Gère le cycle de vie du session token
- Cache token en mémoire (le workflow n8n appelle le client une fois par run)
- `get_valid_token() → str` (re-login si expiré)

### `Order` (Pydantic)

```python
class Order(BaseModel):
    doc_entry: int       # = DocEntry SAP
    doc_num: str         # = DocNum SAP
    card_code: str
    card_name: str
    doc_total: Decimal
    doc_date: date
    update_date: datetime
```

## Stack

- `httpx` (async-ready, future-proof)
- `tenacity` (retry exponentiel)
- `pydantic` v2 (modèles + validation)
- `structlog` (logs JSON)
- `respx` + `pytest` (tests)

## Patterns

### Retry (tenacity)

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((SapTimeoutError, httpx.HTTPStatusError))
)
def _get(self, path: str, params: dict) -> httpx.Response:
    ...
```

### Pagination

```python
def get_orders_since(self, ts: datetime) -> list[Order]:
    orders = []
    next_link = f"/Orders?$filter=UpdateDate gt {ts.isoformat()}&$top=100"
    while next_link:
        resp = self._get(next_link)
        data = resp.json()
        orders.extend(Order(**o) for o in data["value"])
        next_link = data.get("@odata.nextLink")
    return orders
```

### Auth lazy

```python
def _request(self, method, path, **kwargs):
    headers = {"Cookie": f"B1SESSION={self.auth.get_valid_token()}"}
    resp = self.http.request(method, path, headers=headers, **kwargs)
    if resp.status_code == 401:
        self.auth.invalidate()
        headers["Cookie"] = f"B1SESSION={self.auth.get_valid_token()}"
        resp = self.http.request(method, path, headers=headers, **kwargs)
    return resp
```

## Tests

### Unit (sans I/O réel)

- Mock httpx via `respx`
- 1 test par méthode publique
- Couvre : happy path, 401 auto-retry, pagination, 5xx retry, schéma invalide

### Integration (sur staging ACME, VPN requis)

- 1 test : `test_get_orders_real_sap` → fetch 24h
- Skip si pas de VPN (`pytest.mark.skipif`)

### E2E

- Run du workflow n8n complet avec ce client
- Couvert par spec [003-error-handler/tests](../003-error-handler/)

## Logging

Toutes les méthodes publiques :

```python
log.info("sap.fetch.start", method="get_orders_since", since=ts.isoformat())
# ... appel API ...
log.info("sap.fetch.success", count=len(orders), duration_ms=...)
# OU
log.error("sap.fetch.failed", error=str(e), retries=3)
```

## Estimation effort

| Tâche                           | Estimation         |
| ------------------------------- | ------------------ |
| Setup module + http wrapper     | 2h                 |
| AuthManager + tests             | 3h                 |
| `get_orders_since` + pagination | 4h                 |
| `get_order_lines`               | 1h                 |
| Tests unitaires complets        | 3h                 |
| Tests d'intégration             | 2h                 |
| Documentation                   | 1h                 |
| **Total**                       | **~16h** (2 jours) |
