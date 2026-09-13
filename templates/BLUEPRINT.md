# BLUEPRINT.md
> Documento descriptivo — Producido por P1 (ADACG). No editar manualmente; regenerar con P1 o actualizar con P3.

Proyecto: [nombre]
Versión: [N]
Fecha de auditoría: [YYYY-MM-DD]
Fuentes analizadas: [lista de repos / PDFs / specs ingestados]
Arquitecto responsable: [nombre]

---

## 1. VISIÓN GENERAL DEL SISTEMA

> ¿Qué problema resuelve este sistema? ¿Quiénes son sus usuarios?

[descripción de 2-4 párrafos — qué hace el sistema, para quién, en qué contexto]

---

## 2. ARQUITECTURA Y STACK

### Patrón arquitectónico detectado
- **Patrón principal:** [Clean Architecture / Hexagonal / Layered / Event-driven / etc.]
- **Patrones complementarios:** [lista]
- **Paradigma de comunicación:** [REST / GraphQL / Events / RPC / mixto]

### Stack tecnológico (con versiones)

| Capa | Tecnología | Versión | Evidencia |
|------|-----------|---------|-----------|
| Runtime | [ej. Node.js / Python / Go] | [x.y.z] | [OBSERVADO: package.json] |
| Framework | [ej. FastAPI / Express / NestJS] | [x.y.z] | [OBSERVADO: requirements.txt] |
| Base de datos principal | [ej. PostgreSQL] | [x.y] | [OBSERVADO: docker-compose.yml] |
| Caché | [ej. Redis] | [x.y] | [INFERIDO] |
| Auth | [ej. JWT / OAuth2] | — | [OBSERVADO: src/auth/] |
| CI/CD | [ej. GitHub Actions] | — | [OBSERVADO: .github/workflows/] |
| Infraestructura | [ej. Docker / K8s / Railway] | — | [OBSERVADO: Dockerfile] |

### Configuración de Persistencia y Concurrencia (Especial SQLite)
> Si el sistema utiliza SQLite, auditar obligatoriamente los parámetros de concurrencia en la cadena de conexión / DSN para evitar errores de bloqueo *"database is locked"*:

| Parámetro SQLite | Valor Recomendado | Estado en Sistema | Evidencia |
|---|---|---|---|
| **Modo Journal** | `_journal_mode=WAL` (lecturas simultáneas sin bloqueo) | [WAL / DELETE (Inseguro)] | [OBSERVADO: DSN / PRAGMA] |
| **Busy Timeout** | `_busy_timeout=5000` (espera activa ≥ 5s) | [5000ms / AUSENTE] | [OBSERVADO: DSN] |
| **Synchronous** | `_synchronous=NORMAL` (escritura 10x más rápida) | [NORMAL / FULL] | [OBSERVADO: DSN / PRAGMA] |
| **Bloqueo Transaccional** | `_txlock=immediate` (previene deadlocks) | [immediate / deferred] | [OBSERVADO: DSN] |
| **Pool Conexiones (Go)** | `db.SetMaxOpenConns(1)` o 1 writer / N readers | [1 writer pool / ilimitado (Riesgo)] | [OBSERVADO: db.go] |

*Regla de Auditoría:* Si SQLite usa `DELETE journal` por defecto o carece de `_busy_timeout`, marcar de inmediato como `[RIESGO-CRITICO: SQLITE_LOCK_COLLAPSE]` en la Sección 9 (GAPS).

---

## 3. ESTRUCTURA DE MÓDULOS / BOUNDED CONTEXTS

Para cada módulo o contexto identificado:

### [Nombre del módulo/context]
- **Responsabilidad:** [qué hace]
- **Entidades propias:** [lista]
- **Entidades que NO toca:** [lista]
- **Interfaces/puertos expuestos:** [lista]
- **Dependencias externas:** [lista]
- **Estado de implementación:** [IMPLEMENTADO / AUSENTE / PARCIAL / SIMPLIFICADO]
- **Evidencia:** [OBSERVADO: ruta/archivo o INFERIDO]

---

## 4. FLUJO DE DATOS PRINCIPAL

> Trazar el camino crítico de una petición típica end-to-end.

```
[Cliente] → [API Gateway / BFF] → [Módulo A] → [Base de datos]
                                      ↓
                                  [Módulo B] → [Servicio externo]
                                      ↓
                               [Módulo Notif.] → [Email / Push]
```

---

## 5. INTEGRACIONES EXTERNAS

| Integración | Tipo | Auth | Estado | Evidencia |
|-------------|------|------|--------|-----------|
| [servicio] | REST / Webhook / SDK | API Key / OAuth | [VIGENTE / AUSENTE] | [ruta] |

---

## 6. SEGURIDAD Y COMPLIANCE

- **Autenticación:** [mecanismo] [OBSERVADO / INFERIDO]
- **Autorización:** [mecanismo, RBAC/ABAC] [OBSERVADO / INFERIDO]
- **Secrets management:** [.env / Vault / Secrets Manager] [OBSERVADO / INFERIDO]
- **HTTPS / TLS:** [forzado / opcional] [OBSERVADO / INFERIDO]
- **Auditoría/logs:** [estructurados / sin estructura] [OBSERVADO / INFERIDO]

---

## 7. TESTING Y CALIDAD

| Tipo de test | Framework | Cobertura declarada | Estado |
|---|---|---|---|
| Unitarios | [Jest / pytest / etc.] | [%] | [VIGENTE / AUSENTE] |
| Integración | [Supertest / httpx] | [%] | [VIGENTE / AUSENTE] |
| E2E | [Playwright / Cypress] | [%] | [VIGENTE / AUSENTE] |

---

## 8. ANÁLISIS DE NEGOCIO, ENDPOINTS, FLUJO Y PLAN DE MEJORA

### 8.1 Objetivo de Negocio y Qué Busca
- **Propósito central:** [¿Qué problema del mundo real resuelve? ¿Para quién existe?]
- **Beneficiarios / Actores:** [Usuarios finales, administradores, clientes B2B, sistemas externos]
- **Qué busca (Impacto Estratégico):** [Reducción de costos / automatización / time-to-market / cumplimiento]

### 8.2 Qué Hace (Capacidades Operativas)
- **Capacidad 1:** [descripción de proceso clave end-to-end]
- **Capacidad 2:** [descripción]
- **Capacidad 3:** [descripción]

### 8.3 Qué Mide (KPIs y Telemetría de Negocio)
- **Métricas de éxito de negocio:** [ej. tasa de conversión, tiempo medio de resolución, volumen diario]
- **Telemetría operativa:** [ej. latencia P95 < 200ms, tasa de error 5xx < 0.1%, throughput req/s]

### 8.4 Catálogo de Endpoints y Superficie de Exposición

| Método | Ruta | Bounded Context | Auth / Rol | Contrato Entrada | Contrato Salida | Estado |
|--------|------|-----------------|------------|------------------|-----------------|--------|
| POST | `/api/v1/auth/login` | Auth | Público (Rate limited) | `LoginRequestDTO` | `TokenResponseDTO` | [OBSERVADO] |
| GET | `/api/v1/recursos` | Core | Bearer (User/Admin) | Query params | `PaginatedListDTO` | [OBSERVADO] |

### 8.5 Estructura y Flujo de Datos End-to-End

```
[Request / Trigger] 
       │
       ▼
[Gateways & Middlewares] ──► (CORS, Rate Limit, Auth, Sanitización OWASP)
       │
       ▼
[Servicios de Dominio]   ──► (Lógica pura, invariantes de negocio)
       │
       ▼
[Persistencia & Salida]  ──► (DB, Colas, APIs externas) ──► [Response / Evento]
```

### 8.6 Plan de Mejora Accionable

| Nivel | Iniciativa / Mejora | Justificación de Negocio / Arquitectura | Prioridad |
|-------|---------------------|-----------------------------------------|-----------|
| **Inmediato (Quick Wins)** | [ej. añadir rate limiting en login, índices DB] | Prevenir ataques de fuerza bruta y reducir latencia | P0 |
| **Mediano Plazo** | [ej. desacoplar módulo de pagos con eventos] | Eliminar dependencia síncrona y mejorar resiliencia | P1 |
| **Largo Plazo** | [ej. Disaster Recovery automatizado, multi-región] | Garantizar continuidad de negocio y RPO < 1h | P2 |

---

## 9. GAPS Y CONFLICTOS DETECTADOS

> Sección clave para el gate de aprobación humana (Sección 10).

| ID | Tipo | Descripción | Impacto | Prioridad |
|----|------|-------------|---------|-----------|
| GAP-001 | [AUSENTE / CONFLICTO / INFERIDO] | [descripción] | [Alto / Medio / Bajo] | [P0 / P1 / P2] |

---

## 10. GATE DE APROBACIÓN (completar antes de P2)

- [ ] El Blueprint refleja fielmente lo que el sistema ES hoy (no lo que debería ser).
- [ ] Todos los CONFLICTOS tienen decisión pendiente documentada.
- [ ] Los GAPS críticos (P0) tienen owner asignado.
- [ ] El Arquitecto responsable aprobó este documento.

**Aprobado por:** [nombre] **Fecha:** [YYYY-MM-DD]

---

## 11. HISTORIAL DE REVISIONES

| Versión | Fecha | Autor | Cambio |
|---------|-------|-------|--------|
| 1.0 | [fecha] | [autor] | Generación inicial por P1 ADACG |
| 1.x | [fecha] | [autor / P3] | [descripción del cambio] |
