# API Contract: Health Check

**Base URL**: `/api/v1`
**Content-Type**: `application/json`

## GET /health

Required by Constitution Principle VII (Observability).

### Response — 200 OK

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "database": "ok",
    "llm_provider": "ok"
  }
}
```

### Response — 503 Service Unavailable

```json
{
  "status": "degraded",
  "version": "0.1.0",
  "checks": {
    "database": "ok",
    "llm_provider": "unreachable"
  }
}
```
