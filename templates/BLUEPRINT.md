# BLUEPRINT.md
> Documento vivo descriptivo — Producido por P1 (Discovery & Audit) y actualizado continuamente por P07. Refleja fielmente el estado real del sistema observado en código.

Proyecto: [nombre]
Versión: [N]
Fecha de auditoría: [YYYY-MM-DD]
Fuentes analizadas: [lista de repos / rutas / commits auditados]
Arquitecto responsable: [nombre]

---

## 1. VISIÓN GENERAL DEL SISTEMA

> ¿Qué problema resuelve este sistema? ¿Quiénes son sus usuarios y beneficiarios?

[descripción de 2-4 párrafos — qué hace el sistema, para quién, en qué contexto operativo]

---

## 2. ARQUITECTURA, GOBERNANZA Y STACK

### Patrón arquitectónico y gobernanza ARQ-01
- **Patrón principal:** [Vertical Slice Architecture / Hexagonal Condicional / Modular Monolith]
- **Alineación con Artículo ARQ-01:** [Vertical Slices por defecto / Umbral de dominio rico respetado / Persistencia pragmática]
- **Paradigma de comunicación:** [REST / Server-Driven UI (HTMX/Alpine) / Eventos / RPC]

### Stack tecnológico observado

| Capa | Tecnología | Versión | Evidencia |
|---|---|---|---|
| Runtime | [ej. Go / Python / Node.js] | [x.y.z] | [OBSERVADO: go.mod / pyproject.toml / package.json] |
| Framework / Web | [ej. Net/HTTP / FastAPI / Express] | [x.y.z] | [OBSERVADO] |
| Frontend / UI | [ej. HTMX + Alpine.js / Jinja2 / TSX] | [x.y.z] | [OBSERVADO] |
| Base de datos principal | [ej. SQLite / PostgreSQL] | [x.y] | [OBSERVADO] |
| Caché / Mensajería | [ej. Redis / NATS / Ninguno] | [x.y] | [OBSERVADO] |
| Auth & Seguridad | [ej. Sessions / JWT / OAuth2] | — | [OBSERVADO] |
| Empaquetado & Higiene | [ej. //go:embed / Dockerfile] | — | [OBSERVADO] |

### Configuración de Persistencia y Concurrencia (Especial SQLite)
> Si el sistema utiliza SQLite, auditar obligatoriamente los parámetros en la conexión para evitar errores de bloqueo:

| Parámetro SQLite | Valor Requerido (ARQ-01) | Valor en Sistema | Estado | Evidencia |
|---|---|---|---|---|
| **Modo Journal** | `_journal_mode=WAL` | [WAL / DELETE] | [CUMPLE / RIESGO] | [OBSERVADO: DSN / PRAGMA] |
| **Busy Timeout** | `_busy_timeout=5000` (≥ 5s) | [5000ms / AUSENTE] | [CUMPLE / RIESGO] | [OBSERVADO: DSN] |
| **Synchronous** | `_synchronous=NORMAL` | [NORMAL / FULL] | [CUMPLE / RIESGO] | [OBSERVADO: DSN / PRAGMA] |
| **Bloqueo Transaccional** | `_txlock=immediate` | [immediate / deferred] | [CUMPLE / RIESGO] | [OBSERVADO: DSN] |
| **Pool Conexiones** | 1 writer pool / N readers | [1 writer / Ilimitado] | [CUMPLE / RIESGO] | [OBSERVADO: db.go] |

---

## 3. ESTRUCTURA DEL SISTEMA: SLICES VERTICALES Y DOMINIOS RICOS

> El sistema se documenta por **Slices Funcionales Cohesivos** (rutas, storage y templates independientes) y, si superan el umbral de complejidad, por **Módulos de Dominio Rico**.

### 3.1 Catálogo de Slices Verticales (Features Autónomos)

Para cada Slice Vertical activo:

#### Slice: [Nombre del Slice, ej. `features/reuniones`]
- **Propósito & Historias de Usuario:** [Qué necesidad de usuario atiende, ej. US-01]
- **Archivos del Slice:**
  - Control / Handlers: `[ruta, ej. features/reuniones/handler.go]`
  - Almacenamiento / Queries: `[ruta, ej. features/reuniones/storage.go]`
  - Plantillas Higiénicas: `[ruta, ej. views/reuniones/list.html]`
- **Entidades / Tablas Propias:** `[lista de tablas que administra]`
- **Contratos / Endpoints Expuestos:**
  - `[METODO] /ruta` ── Retorna: `[HTML Fragment / JSON / Redirección]`
- **Validación de Higiene y Seguridad:**
  - Sentencias preparadas: `[SÍ / NO]`
  - Plantillas desacopladas (.html empaquetadas): `[SÍ / NO]`
  - Escape contextual anti-XSS: `[SÍ / NO]`
- **Evidencia Observable:** `[OBSERVADO: test pasando o log de ejecución]`

---

### 3.2 Módulos de Dominio Rico (Hexagonal Condicional — Solo si aplica)

> Aplicable únicamente a submódulos que superen el umbral constitucional de >15 reglas de negocio, cálculos de alta complejidad o máquinas de estado multifase.

#### Módulo: [Nombre del Dominio Rico, ej. `core/motor_liquidaciones`]
- **Justificación Constitucional:** [¿Por qué requiere aislamiento de dominio?]
- **Entidades y Value Objects Puros:** [lista de modelos sin dependencias de I/O]
- **Puertos de Entrada (Use Cases):** [interfaces de aplicación]
- **Puertos de Salida (Repositorios/Adapters):** [interfaces de infraestructura]
- **Cobertura de Tests Unitarios:** `[% de cobertura sobre reglas puras]`

---

## 4. FLUJO DE DATOS END-TO-END

### Flujo Estándar: Slice Vertical (CRUD / Mínima Indirección)
```
[Navegador / HTMX] 
       │ HTTP Request (GET/POST)
       ▼
[Middlewares de Seguridad] ──► (Auth, CSRF, Rate Limiting, Logging)
       │
       ▼
[Feature Slice Handler]   ──► (Validación de entrada, bind DTO)
       │
       ▼
[Direct Storage / SQL]    ──► (Sentencia preparada contra DB WAL)
       │ Result Set
       ▼
[Template Engine]         ──► (Renderizado higiénico con auto-escape XSS)
       │ HTML Fragment / Response
       ▼
[Cliente UI]              ──► (Swap reactivo vía HTMX / Alpine)
```

### Flujo con Dominio Rico (Solo submódulos de alta complejidad)
```
[Handler / Controller] ──► [Input Port] ──► [Domain Model / Invariantes]
                                                   │
                                            [Output Port]
                                                   │
                                            [Infrastructure / DB Adapter]
```

---

## 5. CATÁLOGO DE ENDPOINTS Y SUPERFICIE DE EXPOSICIÓN

| Método | Ruta | Slice Responsable | Auth / Permiso | Formato Respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/reuniones` | `features/reuniones` | Sesión activa | HTML (Página completa) | [OBSERVADO] |
| POST | `/reuniones` | `features/reuniones` | Rol Admin/Organizador | HTML (Fragmento) / 303 | [OBSERVADO] |
| POST | `/acuerdos` | `features/acuerdos` | Miembro reunión | HTML Fragment (HTMX swap)| [OBSERVADO] |

---

## 6. INTEGRACIONES EXTERNAS

| Integración | Propósito | Mecanismo | Auth | Estado | Evidencia |
|---|---|---|---|---|---|
| [Servicio A] | [ej. Notificaciones Email] | SMTP / REST | API Key / Env | [VIGENTE / AUSENTE] | [ruta/archivo] |

---

## 7. SEGURIDAD Y COMPLIANCE

- **Parametrización SQL:** [100% verificado / Infracciones detectadas]
- **Higiene XSS:** [Escape contextual activo en templates / Cero raw concatenation]
- **Autenticación & Autorización:** [Mecanismo RBAC / Sesiones seguras / Tokens]
- **Gestión de Secretos:** [Cero secrets en git / variables de entorno vía .env]
- **Auditoría de Logs:** [Logs estructurados sin filtración de datos sensibles]

---

## 8. TESTING Y VERIFICACIÓN TERMINAL

| Nivel de Test | Herramienta | Enfoque | Estado | Evidencia Observable |
|---|---|---|---|---|
| Unitario (Dominio) | [go test / pytest] | Reglas de negocio e invariantes | [VIGENTE] | [Pass: X tests en Y ms] |
| Integración (Slices)| [go test / supertest] | Handlers + DB en memoria/WAL | [VIGENTE] | [Pass: X tests en Y ms] |
| End-to-End / Smoke | [curl / headless] | HTTP status y swaps HTMX | [VIGENTE] | [HTTP 200 OK en rutas clave] |

---

## 9. GAPS Y DEUDA TÉCNICA DETECTADA

| ID | Tipo | Descripción | Impacto | Prioridad | Plan de Remediación |
|---|---|---|---|---|---|
| GAP-001 | [ARQ-01 / SEGURIDAD / PERFORMANCE] | [descripción del gap detectado] | [Alto / Medio / Bajo] | [P0 / P1 / P2] | [Acción concreta] |

---

## 10. GATE DE CERTIFICACIÓN ARQUITECTÓNICA

- [ ] El Blueprint refleja fielmente el código observado en disco (cero alucinaciones).
- [ ] La estructura de slices y componentes cumple con la CONSTITUTION (Artículo ARQ-01).
- [ ] No existen vulnerabilidades críticas (SQL injection, XSS o secrets expuestos).
- [ ] Todas las tareas de slices cuentan con evidencia observable en terminal.

**Auditor / Arquitecto responsable:** [nombre]  
**Fecha:** [YYYY-MM-DD]

---

## 11. HISTORIAL DE REVISIONES

| Versión | Fecha | Autor | Modo Motor | Resumen del Cambio |
|---|---|---|---|---|
| 1.0 | [fecha] | [autor] | Standalone / Gentle-AI | Generación inicial por Discovery (P01) |
| 1.1 | [fecha] | [autor] | ODD Streamlined | Consolidación de nuevos slices verticales |
