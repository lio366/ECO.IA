# 📡 ECO-IA — Referencia de API

**Base URL:** `http://135.148.232.10:8000`  
**Docs interactivos:** `http://135.148.232.10:8000/docs`

---

## Autenticación

### API Key (servicios)

```
Header: X-API-Key: TU_API_KEY
```

### Admin Key (administración)

```
Header: X-Admin-Key: TU_ADMIN_KEY
```

---

## Endpoints públicos

### `GET /`

```bash
curl http://135.148.232.10:8000/
# {"status":"ok","system":"ECO-IA","version":"1.0.0","server":"135.148.232.10"}
```

### `GET /health`

```bash
curl http://135.148.232.10:8000/health
# {"status":"healthy"}
```

---

## Servicios (requiere `X-API-Key`)

### `POST /api/v1/services/ai/complete`

Completado de texto con IA (GPT-4o-mini o Ollama).

```bash
curl -X POST http://135.148.232.10:8000/api/v1/services/ai/complete \
  -H "X-API-Key: TU_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Escribe un resumen de ECO-IA en 2 líneas",
    "model": "gpt-4o-mini",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

**Respuesta:**

```json
{
  "result": "ECO-IA es un servidor autónomo...",
  "model": "gpt-4o-mini",
  "tokens_used": null
}
```

---

### `POST /api/v1/services/data/process`

Procesamiento de datos con IA.

```bash
curl -X POST http://135.148.232.10:8000/api/v1/services/data/process \
  -H "X-API-Key: TU_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"ventas": [100, 200, 150], "mes": "junio"},
    "operation": "summarize"
  }'
```

**Respuesta:**

```json
{
  "status": "processed",
  "operation": "summarize",
  "input_type": "dict",
  "result": "Processing of 'summarize' completed."
}
```

---

### `GET /api/v1/services/hosting/plans`

Lista de planes disponibles con precios actuales.

```bash
curl http://135.148.232.10:8000/api/v1/services/hosting/plans \
  -H "X-API-Key: TU_KEY"
```

**Respuesta:**

```json
{
  "plans": [
    {"plan_key": "basic", "name": "Basic", "base_price_usd": 9.99,
     "current_price_usd": 9.99, "api_calls_per_month": 10000},
    {"plan_key": "pro", "name": "Pro", "base_price_usd": 49.99,
     "current_price_usd": 49.99, "api_calls_per_month": 100000},
    {"plan_key": "enterprise", "name": "Enterprise", "base_price_usd": 199.99,
     "current_price_usd": 199.99, "api_calls_per_month": 1000000}
  ]
}
```

---

### `GET /api/v1/services/hosting/ip-pricing`

Catálogo de precios IP de OVHcloud US en USD.

```bash
curl http://135.148.232.10:8000/api/v1/services/hosting/ip-pricing \
  -H "X-API-Key: TU_KEY"
```

**Respuesta:**

```json
{
  "provider": "OVHcloud US",
  "region": "US",
  "currency": "USD",
  "prices_include_tax": false,
  "catalog_id": "GE-A8CCF",
  "categories": {
    "cloud": [
      {"product": "Floating IPv4", "monthly_price_usd": 3.5},
      {"product": "Floating IPv6", "monthly_price_usd": 1.5}
    ]
  }
}
```

---

### `GET /api/v1/services/hosting/status`

Estado del servicio de hosting.

```bash
curl http://135.148.232.10:8000/api/v1/services/hosting/status \
  -H "X-API-Key: TU_KEY"
# {"status":"operational","uptime_pct":99.9}
```

---

## Admin (requiere `X-Admin-Key`)

### `GET /api/v1/admin/health`

Estado completo de todos los agentes.

```bash
curl http://135.148.232.10:8000/api/v1/admin/health \
  -H "X-Admin-Key: TU_ADMIN_KEY"
```

**Respuesta:**

```json
{
  "status": "healthy",
  "agents": {
    "orchestrator": "active",
    "monetization": "active",
    "devops": "active",
    "resources": "active",
    "security": "active",
    "analytics": "active"
  }
}
```

---

### `GET /api/v1/admin/metrics`

Métricas en tiempo real del servidor.

```bash
curl http://135.148.232.10:8000/api/v1/admin/metrics \
  -H "X-Admin-Key: TU_ADMIN_KEY"
```

**Respuesta:**

```json
{
  "cpu_percent": 23.4,
  "ram_percent": 41.2,
  "ram_used_gb": 3.1,
  "ram_total_gb": 7.6,
  "disk_percent": 8.5,
  "disk_used_gb": 4.1,
  "disk_total_gb": 47.4
}
```

---

### `GET /api/v1/admin/agents`

Lista de agentes registrados.

```bash
curl http://135.148.232.10:8000/api/v1/admin/agents \
  -H "X-Admin-Key: TU_ADMIN_KEY"
```

---

### `GET /api/v1/admin/scheduler/tasks`

Tareas programadas del scheduler.

```bash
curl http://135.148.232.10:8000/api/v1/admin/scheduler/tasks \
  -H "X-Admin-Key: TU_ADMIN_KEY"
```

---

### `GET /api/v1/admin/logs`

Últimas 100 líneas de logs del sistema.

```bash
curl http://135.148.232.10:8000/api/v1/admin/logs \
  -H "X-Admin-Key: TU_ADMIN_KEY"
```

---

## Webhooks

### `POST /api/v1/webhooks/stripe`

Recibe eventos de Stripe. Configurar en Stripe Dashboard.

**Eventos soportados:**

| Evento | Descripción |
|--------|-------------|
| `customer.subscription.created` | Nueva suscripción creada |
| `customer.subscription.deleted` | Suscripción cancelada |
| `invoice.payment_succeeded` | Pago exitoso |
| `invoice.payment_failed` | Pago fallido |

---

## Rate Limiting

- **Límite:** 100 requests/minuto por IP
- **Headers de respuesta:**
  - `X-RateLimit-Limit: 100`
  - `X-RateLimit-Remaining: 87`

**Error 429:**

```json
{
  "detail": "Rate limit exceeded. Max 100 requests/min.",
  "retry_after": 45
}
```

---

## Códigos de error

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `400` | Bad Request (payload inválido) |
| `401` | API Key inválida o faltante |
| `403` | Admin Key inválida o faltante |
| `429` | Rate limit excedido |
| `503` | Servicio no disponible (LLM error) |
