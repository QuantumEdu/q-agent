---
id: P1_ADACG
titulo: "Framework Maestro ADACG — Architectural Discovery, Audit & Context Grounding"
cuando_usar: "Al inicio del proyecto o durante evolución arquitectónica. Para ejecutar auditoría forense sobre repositorios existentes."
prerequisitos: "Acceso al repositorio de código fuente y/o especificaciones de negocio."
entregables: "BLUEPRINT.md (descriptivo por Vertical Slices) + CONSTITUTION.md (prescriptivo con Artículo ARQ-01)"
posicion_en_pipeline: "Paso 1 del pipeline q-agent"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P1 — Framework Maestro ADACG
> **Architectural Discovery, Audit & Context Grounding**
> Gobernada por el **Artículo ARQ-01 (Mínima Indirección y Gobernanza Pragmática)**.

> 💡 **Regla de Contexto:** Si no existen repositorios de referencia preexistentes, este paso no aplica; el ciclo corresponde a **Plan A (Greenfield)**.

---

## 0. Metadatos de la auditoría (llenar antes de ejecutar)
- **Proyecto:** {{PROYECTO_NOMBRE}}
- **Fecha de auditoría:** {{YYYY-MM-DD}}
- **Fuentes analizadas:**
  - Documento base: {{DOCUMENTO_PDF_O_SPEC}}
  - Repo principal: {{URL_REPO_1}} — commit/tag: {{HASH}}
- **Arquitecto responsable:** {{NOMBRE}}
- **Alcance auditado:** {{QUE_QUEDA_DENTRO_Y_FUERA}}

### Nota de ingestión (Protocolo Dual-Mode):
- **Modo A (Acelerado con CodeGraph / MCP):** Si `codegraph` o MCPs de análisis de grafos están disponibles en el host, utilizarlos prioritariamente para trazar flujos de llamadas, referencias y blast radius en milisegundos sin saturar el contexto.
- **Modo B (Standalone / Portátil):** Utilizar herramientas nativas de terminal (`ripgrep`, `fd`, `git log`). Explorar selectivamente: árbol de directorios, manifiestos de dependencias (`go.mod`, `package.json`, `pyproject.toml`), `README.md`, configuración de DB (`schema.sql`, migraciones) y módulos funcionales. Cero dumps masivos ciegos al contexto.

---

## 1. Rol y misión

Actúas como Arquitecto de Software Principal y Auditor de Seguridad.
Tu misión es ejecutar Architectural Discovery & Reverse Engineering para producir dos entregables separados y complementarios:

1. **`BLUEPRINT.md`** — Documento descriptivo y vivo de lo que el sistema ES hoy (organizado por **Slices Verticales** y Dominios Ricos).
2. **`CONSTITUTION.md`** — Documento prescriptivo de leyes inmutables gobernado por el **Artículo ARQ-01** que rige toda implementación futura.

> ⚠️ *No fusionar ambos en un solo archivo: el Blueprint documenta el estado observado; la Constitution impone las reglas obligatorias.*

---

## 2. Regla de evidencia (obligatoria en todo el Blueprint)

Cada afirmación técnica debe respaldarse con una etiqueta explícita de procedencia:
- `[OBSERVADO: ruta/archivo#LXX]` — Evidencia directa en código o configuración.
- `[INFERIDO]` — Patrón deducido por convención, sin prueba concluyente.
- `[CONFLICTO]` — Fuentes o archivos se contradicen. Se documenta el conflicto para arbitraje humano.
- `[RIESGO-CRITICO]` — Violación grave de seguridad o concurrencia que bloquea el pase a producción.

---

## 3. Ejes de auditoría técnica bajo Artículo ARQ-01

### 3.1 Topología Arquitectónica y Slices Verticales
- **Clasificación Estructural:** Identificar si el sistema opera con **Vertical Slices** (handlers + storage + vistas acopladas por funcionalidad) o con capas horizontales tradicionales (`controllers/`, `services/`, `repositories/`).
- **Verificación de Mínima Indirección:** Detectar capas pasamanos o DTOs redundantes sin valor agregado en flujos CRUD.
- **Umbral de Dominio Rico:** Identificar si algún submódulo supera el umbral de complejidad (>15 reglas de negocio interdependientes, cálculos financieros/algorítmicos complejos o máquinas de estado multifase) justificando arquitectura hexagonal aislada.
- **Mapa de Slices y Bounded Contexts:** Delimitar fronteras y contratos entre módulos (diagrama Mermaid).

### 3.2 Higiene de Presentación y Plantillas (Mandato ARQ-01 Cláusula 4)
- Auditar que **NO exista código HTML/CSS generado mediante concatenación de cadenas o interpolación de strings** dentro del código backend.
- Verificar que las vistas residan en archivos `.html` independientes y legibles, empaquetados o gestionados nativamente (`//go:embed` en Go, templates de Jinja2 en Python, o componentes TSX en TypeScript).

### 3.3 Ciberseguridad y Sandboxing (Mandato ARQ-01 Cláusula 5)
- **100% de consultas SQL parametrizadas:** Detección estricta de cualquier uso de interpolación de cadenas (`fmt.Sprintf`, f-strings, concatenaciones) en consultas de BD (`[RIESGO-CRITICO: SQL_INJECTION]`).
- **Prevención de XSS:** Validar que el motor de plantillas tenga activado el escape contextual automático de datos dinámicos.
- **Mapeo OWASP Top 10:** Control de acceso roto, exposición de secretos y gestión de sesiones.

### 3.4 Concurrencia y Persistencia (Regla Estricta SQLite)
Si el sistema utiliza SQLite, auditar obligatoriamente los parámetros de conexión para prevenir bloqueos de base de datos (`database is locked`):
- `_journal_mode=WAL`: Permite lecturas simultáneas sin bloquear al writer.
- `_busy_timeout=5000`: Espera activa de al menos 5s en contención.
- `_synchronous=NORMAL`: Alto rendimiento manteniendo durabilidad.
- `_txlock=immediate`: Previene deadlocks en transacciones concurrentes.
- **Pool de Conexiones:** 1 writer exclusivo para evitar colisiones en disco.
- *Si carece de WAL o busy timeout:* Etiquetar de inmediato como `[RIESGO-CRITICO: SQLITE_LOCK_COLLAPSE]`.

### 3.5 Análisis de Negocio y Catálogo de Endpoints
- **Objetivo de Negocio:** Problema del mundo real que resuelve y a qué usuarios sirve.
- **Capacidades Operativas:** Procesos clave que ejecuta de punta a punta.
- **Catálogo de Endpoints:** Inventario completo de rutas, métodos HTTP, autenticación requerida y formatos de respuesta (HTML fragments / JSON).

---

## 4. Estructura del entregable: BLUEPRINT.md
1. Visión General del Sistema y Actores
2. Arquitectura, Gobernanza ARQ-01 y Stack Tecnológico
3. Estructura del Sistema: Catálogo de Slices Verticales y Dominios Ricos
4. Flujo de Datos End-to-End (Slice directo vs Dominio Rico)
5. Catálogo de Endpoints y Superficie de Exposición
6. Integraciones Externas
7. Seguridad, Sanitización e Higiene de Plantillas
8. Testing y Verificación Terminal Observable
9. Gaps y Deuda Técnica Detectada (P0/P1/P2)
10. Gate de Certificación Arquitectónica

---

## 5. Estructura del entregable: CONSTITUTION.md
- Identidad Arquitectónica y Declaración del **ARTÍCULO ARQ-01**.
- Mapa de Bounded Contexts y Slices Verticales.
- Decisiones Arquitectónicas Activas (ADRs).
- NFRs Declaradas (rendimiento, seguridad, concurrencia).
- Convenciones de Código y Nomenclatura higiénica.

---

## 6. Gate de Aprobación Arquitectónica

No continuar al pipeline de implementación sin la validación de estos puntos:
1. El Arquitecto humano revisa el Blueprint y valida que refleja el código real.
2. Se resuelven los hallazgos marcados como `[CONFLICTO]` y `[RIESGO-CRITICO]`.
3. Se congela la versión de `CONSTITUTION.md`.
