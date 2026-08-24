# AGENTS — ECO-IA

Este documento describe los agentes autónomos del sistema ECO-IA y sus responsabilidades.

## 1. Orchestrator Agent (Master)
- Coordina tareas entre agentes.
- Prioriza incidencias y jobs de negocio.
- Consolida estado global del sistema.
- Publica métricas de salud general.

## 2. Monetization Agent
- Gestiona catálogo de servicios.
- Calcula precios dinámicos.
- Coordina facturación con Stripe.
- Reporta MRR, conversión y churn.

## 3. DevOps Agent
- Supervisa despliegues y reinicios seguros.
- Ejecuta backups programados.
- Gestiona auto-healing básico.
- Verifica salud de contenedores.

## 4. Resources Agent
- Monitorea CPU/RAM/Disco/Red.
- Sugiere o ejecuta optimizaciones.
- Gestiona limpieza de logs y temporales.
- Detecta riesgo de saturación.

## 5. Security Agent
- Audita accesos y eventos.
- Verifica políticas de firewall.
- Detecta patrones sospechosos.
- Emite alertas de seguridad.

## 6. Analytics Agent
- Agrega KPIs de negocio y técnicos.
- Detecta anomalías de uso e ingresos.
- Genera reportes periódicos.
- Entrega recomendaciones accionables.

---

## Contrato base de agente

Cada agente debe implementar:
- `start()`
- `stop()`
- `health_check()`
- `execute(task: dict) -> dict`

## Comunicación entre agentes
- Canal recomendado: Redis Pub/Sub.
- Convención de canales:
  - `ecoia.events.*`
  - `ecoia.tasks.*`
  - `ecoia.alerts.*`

## Estándar de logging
- Formato JSON estructurado.
- Campos mínimos:
  - `timestamp`
  - `agent`
  - `level`
  - `event`
  - `trace_id`
  - `payload`

## Reglas operativas
- Ningún agente bloquea el ciclo completo.
- Timeouts por tarea obligatorios.
- Reintentos con backoff exponencial.
- Idempotencia en acciones críticas (pagos, backups, bloqueos IP).
