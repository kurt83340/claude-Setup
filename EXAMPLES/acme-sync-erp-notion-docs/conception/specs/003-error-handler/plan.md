# Plan technique — 003 Error Handler

## Architecture

```
src/error_handler/
├── __init__.py
├── classifier.py      # classify(exc) → Category
├── notifier.py        # send_email_alert, capture_sentry
├── state.py           # Tracking erreurs récentes (n8n Data Table)
└── exceptions.py      # Hierarchy : SyncError → Retryable/Fatal/Ignorable
```

## Hierarchy exceptions

```python
class SyncError(Exception):
    """Base."""

class RetryableError(SyncError):
    """Tenacity retry."""

class FatalError(SyncError):
    """Stop + alert."""

class IgnorableError(SyncError):
    """Skip + log."""
```

## Logique de classification

```python
def classify(exc: Exception) -> type[SyncError]:
    if isinstance(exc, httpx.TimeoutException):
        return RetryableError
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code in (429, 503, 504):
            return RetryableError
        if exc.response.status_code in (401, 403) and is_persistent(exc):
            return FatalError
    if isinstance(exc, NotionSchemaError):
        return FatalError
    if isinstance(exc, OrderValidationError):
        return IgnorableError
    return FatalError  # par défaut, prudence
```

## Tracking état (n8n Data Table `sync_errors`)

```
Schema :
- timestamp (datetime)
- category (RETRYABLE | FATAL | IGNORABLE)
- error_class (str)
- message (str)
- context (json)
```

Utilisé pour :

- Détecter > 3 erreurs consécutives → alert
- Cooldown 30min entre alertes identiques

## Tests

- 1 test par catégorie d'exception
- Test cooldown (mock datetime)
- Test integration Sentry (capture mock)
- Test email alert (mock SMTP)

## Estimation

| Tâche                    | Estimation |
| ------------------------ | ---------- |
| Setup hierarchy          | 1h         |
| Classifier + tests       | 3h         |
| State tracking n8n       | 2h         |
| Notifier (Sentry + SMTP) | 3h         |
| Tests complets           | 3h         |
| **Total**                | **~12h**   |
