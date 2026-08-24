# 🌱 ECO-IA — Autonomous AI-Agent Server System

> Un servidor **99.9% autónomo** basado en Agentes IA que se **autoabastece**, **genera ingresos** y es **sostenible**. Optimizado para Hetzner VPS.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 ¿Qué es ECO-IA?

ECO-IA es un sistema de servidor autónomo basado en múltiples **Agentes de Inteligencia Artificial** que trabajan 24/7 sin intervención humana para:

1. 🔧 **Autoabastecerse** — monitoreo continuo, auto-recuperación, backups automáticos
2. 💰 **Generar ingresos** — API de IA, hosting, procesamiento de datos (cobrado con Stripe)
3. 🌿 **Ser sostenible** — optimización de recursos, escalado automático, limpieza continua

---

## 🏗️ Arquitectura Multi-Agente

```
┌─────────────────────────────────────────────────────────┐
│                 🌐  Internet / Clientes                  │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
               ┌──────▼──────┐
               │    Nginx    │
               └──────┬──────┘
          ┌───────────▼───────────┐
          │    ECO-IA FastAPI     │
          │   REST API  :8000     │
          └───────────┬───────────┘
                      │
         ┌────────────▼────────────┐
         │   🧠 ORQUESTADOR        │
         │   Coordina todo         │
         └────┬───┬───┬───┬───┬───┘
              │   │   │   │   │
     💰 Monet│ 🔧Dev│ 🌿Res│ 🛡️Sec│ 📊Ana│
              │   │   │   │   │
         ┌────▼───▼───▼───▼───▼────┐
         │       MessageBus         │
         └──────────────────────────┘
```

### Los 6 Agentes

| Agente | Función |
|--------|---------|
| 🧠 **Orquestador** | Coordina todos los agentes, decisiones con LLM, reportes ejecutivos |
| 💰 **Monetización** | Clientes, facturación Stripe, pricing dinámico, upselling |
| 🔧 **DevOps** | Deploy automático, auto-healing, backups a Hetzner Storage Box |
| 🌿 **Recursos** | Optimización CPU/RAM, limpieza de logs, auto-scaling |
| 🛡️ **Seguridad** | Firewall dinámico (UFW), detección de intrusiones, auditorías |
| 📊 **Analytics** | Reportes diarios, predicción de anomalías, dashboard |

---

## 🚀 Inicio Rápido (Hetzner VPS)

### Opción A — Instalación automática (recomendada)

```bash
# En tu VPS Hetzner con Ubuntu 22.04
curl -fsSL https://raw.githubusercontent.com/liorvys1981-sys/ECO-IA/main/scripts/install.sh | sudo bash
```

### Opción B — Instalación manual

```bash
# 1. Clonar repositorio
git clone https://github.com/liorvys1981-sys/ECO-IA.git /opt/eco-ia
cd /opt/eco-ia

# 2. Configurar entorno
cp .env.example .env
nano .env  # editar variables

# 3. Iniciar con Docker Compose
docker compose -f docker/docker-compose.yml up -d

# 4. Verificar
curl http://localhost:8000/health
```

---

## ⚙️ Configuración

### Variables de entorno esenciales (`.env`)

```bash
# API
ECO_IA_API_KEY=tu-clave-api-segura
ECO_IA_ADMIN_KEY=tu-clave-admin-segura

# LLM (elige uno)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-tu-clave

# Pagos
STRIPE_SECRET_KEY=sk_live_tu-clave
STRIPE_WEBHOOK_SECRET=whsec_tu-secreto

# Backups (Hetzner Storage Box)
HETZNER_STORAGE_BOX_HOST=u123456.your-storagebox.de
HETZNER_STORAGE_BOX_USER=u123456

# Alertas por email
SMTP_HOST=smtp.gmail.com
ALERT_EMAILS=admin@tudominio.com
```

---

## 📡 API Endpoints

### Servicios (requiere `X-API-Key`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/services/ai/complete` | Completado de texto con IA |
| `POST` | `/api/v1/services/data/process` | Procesamiento de datos |
| `GET`  | `/api/v1/services/hosting/plans` | Planes disponibles |
| `GET`  | `/api/v1/services/hosting/status` | Estado del hosting |

### Admin (requiere `X-Admin-Key`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/health` | Estado de todos los agentes |
| `GET` | `/api/v1/admin/metrics` | Métricas en tiempo real |
| `GET` | `/api/v1/admin/agents` | Lista de agentes |
| `GET` | `/api/v1/admin/scheduler/tasks` | Tareas programadas |

### Ejemplos

```bash
# Completado de IA
curl -X POST http://localhost:8000/api/v1/services/ai/complete \
  -H "X-API-Key: tu-clave" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Escribe un resumen de IA en 3 líneas", "max_tokens": 150}'

# Ver métricas del servidor
curl http://localhost:8000/api/v1/admin/metrics \
  -H "X-Admin-Key: tu-clave-admin"

# Ver planes disponibles
curl http://localhost:8000/api/v1/services/hosting/plans \
  -H "X-API-Key: tu-clave"
```

---

## 🐳 Docker

```bash
# Iniciar todo el sistema
docker compose -f docker/docker-compose.yml up -d

# Ver estado
docker compose -f docker/docker-compose.yml ps

# Escalar la API
docker compose -f docker/docker-compose.yml up -d --scale eco-ia-api=3

# Ver logs
docker compose -f docker/docker-compose.yml logs -f eco-ia-api

# Detener todo
docker compose -f docker/docker-compose.yml down
```

---

## 📊 Monitoreo

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Grafana** | `http://TU_IP:3000` | Dashboards visuales |
| **Prometheus** | `http://TU_IP:9090` | Métricas en bruto |
| **API Docs** | `http://TU_IP:8000/docs` | Documentación interactiva |

---

## 🧪 Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt

# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html

# Solo agentes
pytest tests/test_agents.py -v

# Solo API
pytest tests/test_api.py -v
```

---

## 🛡️ Seguridad

- **Firewall:** UFW configurado automáticamente (solo puertos necesarios)
- **Fail2Ban:** Protección contra brute-force SSH
- **Rate limiting:** 100 req/min por IP
- **Auth:** API Keys con comparación en tiempo constante (anti-timing attacks)
- **HTTPS:** Certbot/Let's Encrypt (configurar con tu dominio)
- **Auto-block:** IPs maliciosas bloqueadas automáticamente tras 10 intentos fallidos

---

## 📂 Estructura del Proyecto

```
ECO-IA/
├── agents/
│   ├── orchestrator/      # 🧠 Agente Maestro
│   ├── monetization/      # 💰 Agente Monetización
│   ├── devops/            # 🔧 Agente DevOps
│   ├── resources/         # 🌿 Agente Recursos
│   ├── security/          # 🛡️ Agente Seguridad
│   └── analytics/         # 📊 Agente Analytics
├── core/                  # Base: MessageBus, Scheduler, LLMConnector
├── api/                   # FastAPI + middleware + routes
├── config/                # Settings, variables de entorno
├── docker/                # Dockerfile + docker-compose.yml
├── monitoring/            # Prometheus + Grafana + AlertManager
├── scripts/               # install.sh, backup.sh, health_check.sh
├── tests/                 # test_agents.py + test_api.py
├── docs/                  # SETUP_HETZNER.md, AGENTS.md, etc.
├── requirements.txt
└── .env.example
```

---

## 📖 Documentación adicional

| Documento | Descripción |
|-----------|-------------|
| [docs/SETUP_HETZNER.md](docs/SETUP_HETZNER.md) | Guía de instalación paso a paso en Hetzner |
| [docs/AGENTS.md](docs/AGENTS.md) | Documentación de cada agente |
| [docs/MONETIZATION.md](docs/MONETIZATION.md) | Guía de monetización con Stripe |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura técnica completa |

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'feat: añadir nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📄 Licencia

MIT License — libre para uso personal y comercial.

---

*Built with ❤️ for autonomous, sustainable AI infrastructure.* 
