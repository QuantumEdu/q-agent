---
id: P9_CAB_RP
titulo: "CAB-RP 2.0 — Compliance Audit Blueprint & Remediation Plan (ODD & ARQ-01)"
cuando_usar: "Al cierre de un ciclo completo (MVP o N features). ANTES de etiquetar el sistema como production-ready o cortar un release."
prerequisitos: "CONSTITUTION.md (con Artículo ARQ-01), BLUEPRINT.md, bitácoras de tareas ODD (`q-tasks/*.md` o `odd/tasks/*.md`), acceso de solo lectura al repositorio."
entregables: "Documento CAB-RP con: Matriz de Trazabilidad ODD/UAC + Tabla PR-Readiness + Specs EARS por gap + Plan de Remediación priorizado P0/P1."
posicion_en_pipeline: "Compuerta de Auditoría Pre-Release — posterior a P07 y previa a entrega de release"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# CAB-RP 2.0 — Compliance Audit Blueprint & Remediation Plan

> **Misión:** Auditar el sistema construido contra el código real, las bitácoras vivas ODD y el **Artículo Constitucional ARQ-01**, transformando las brechas detectadas en especificaciones formales ejecutables (EARS) y un plan de remediación priorizado.
> **Principio Clave:** Se auditan *invariantes de arquitectura, seguridad y evidencia empírica*, eliminando el dogmatismo burocrático de capas intermedias vacías.

---

## 1. Invariantes Operativos de Auditoría (Heredados de `q-audit-readonly`)

1. **Inmutabilidad Absoluta en Disco:** Auditoría 100% de solo lectura. Queda prohibido modificar el código auditado (`replace_file_content`, `write_to_file`, `git checkout`). Al finalizar, `git status -s` debe permanecer inalterado (salvo el reporte `AUDIT_REPORT.md`).
2. **CodeGraph Primero:** Si `codegraph` o MCPs están disponibles, usarlos prioritariamente para trazar dependencias y blast radius antes de búsquedas ciegas de texto.
3. **Tolerancia Cero a Falsas Completitudes (Anti-Mocking):** Verificar que las tareas marcadas `[x]` en las bitácoras ODD cuenten con registro en la tabla `Terminal Evidence Gate` (código de salida 0 y salida observable). Tareas con datos estáticos simulados o stubs permanentes sin autorización = **`❌ Gap P0 Bloqueante`**.

---

## Fase 1 — Matriz de Trazabilidad ODD y Cumplimiento de UAC

Por cada feature entregada en el sistema, auditar la cadena de valor de negocio a código:

| Verificación | Criterio de Aprobación | Veredicto |
|---|---|---|
| **Bitácora Viva** | Existe bitácora única (`q-tasks/<feature>.md` o `odd/tasks/<feature>.md`) basada en `task-log-template.md`. | `✅ / ❌ Sin bitácora` |
| **Trazabilidad BMAD / UAC** | Las tareas técnicas (`TASK-XX`) atienden directamente a los Criterios de Aceptación de Usuario (`UAC-XX`). | `✅ / ⚠️ Drift parcial` |
| **Terminal Evidence Gate** | Cada checkbox marcado `[x]` cuenta con su comando de terminal, exit code 0 y resultado observado registrado. | `✅ / ❌ Falsa completitud` |
| **Scope Governance** | Toda omisión funcional está registrada y justificada en la sección "Out of Scope". | `✅ / ❌ Scope drift no justificado` |

---

## Fase 2 — Checklist de Production-Readiness

Cada ítem recibe uno de cuatro veredictos:
- `✅ Cumple`: Verificado con evidencia empírica en código (ruta, línea, test o comando).
- `❌ Gap`: Incumplimiento que pasa a Fase 3 (conversión a EARS).
- `⚪ No aplica`: Exclusión justificada explícitamente en el "Out of Scope" de la bitácora.
- `❓ No verificable`: Sin acceso a staging/ambiente de ejecución (requiere decisión humana).

---

### Categoría 0: Arquitectura Constitucional (Artículo ARQ-01)

> ⚖️ **A diferencia de versiones anteriores que exigían 5 capas y 5 patrones fijos, esta auditoría evalúa el cumplimiento de las cláusulas del Artículo ARQ-01.**

1. **Cláusula 1 (Vertical Slices & Mínima Indirección):**
   - Las funcionalidades estándar (CRUD, listados, formularios) residen en Slices Verticales cohesivos.
   - **Criterio Senior:** *Prohibido penalizar la ausencia de interfaces pasamanos o carpetas intermedias vacías.* La ausencia de indirección innecesaria es un mérito, no un defecto.
2. **Cláusula 2 (Umbral de Dominio Rico):**
   - Si un módulo tiene arquitectura hexagonal aislada (`domain/`, `ports/`), verificar que supera el umbral (>15 reglas de negocio complejas o máquinas de estado multifase). Si un CRUD simple fue sobreingeniado en capas pasamanos, marcar como `⚠️ Deuda por Sobreingeniería`.
3. **Cláusula 3 (Persistencia Pragmática & Concurrencia SQLite):**
   - Consultas de lectura directas y optimizadas sin modelos de dominio intermediarios redundantes.
   - **Regla Estricta SQLite (si aplica):**
     - WAL Mode activo (`_journal_mode=WAL`).
     - Busy Timeout configurado (`_busy_timeout=5000` o superior).
     - Synchronous en modo `NORMAL`.
     - Pool controlado (1 writer exclusivo para evitar bloqueos en disco).
     - *Si carece de WAL o busy timeout:* **`❌ Gap P0 Bloqueante`** inmediato.
4. **Cláusula 4 (Higiene de Plantillas y Vistas):**
   - **Cero concatenación de cadenas HTML en código backend:** Las vistas deben residir en archivos `.html` independientes y legibles.
   - Empaquetamiento nativo (`//go:embed` en Go, templates Jinja2 en Python, o componentes TSX en TypeScript).
   - *Concatenaciones de HTML en código:* **`❌ Gap P0`**.
5. **Cláusula 5 (Ciberseguridad Mandatoria & Zero Trust):**
   - **100% de consultas SQL parametrizadas:** Cero interpolaciones de cadenas (`fmt.Sprintf`, f-strings, template literals). Cualquier query con concatenación = **`❌ Gap P0 Inyección SQL`**.
   - **Escape Contextual Anti-XSS:** Motor de plantillas con auto-escape activado en renderizado dinámico.
   - **Zero Secrets:** Cero credenciales o claves API en código fuente.

---

### Categorías Complementarias de Production-Readiness

### 1. Usabilidad e Interfaz UI/UX
- Responsive, contraste de color accesible, jerarquía tipográfica.
- Manejo de estados (hover, disabled, loading, éxito, error).
- Formularios con validación en cliente y servidor con retroalimentación clara.

### 2. Observabilidad y Logs
- Logs estructurados (no prints huérfanos) en caminos críticos.
- Formato consistente (nivel, timestamp, contexto de error).

### 3. Telemetría y Métricas
- Captura de métricas operativas clave (latencia, tasas de error).
- Eventos de negocio críticos instrumentados.

### 4. Versionado y Sincronización
- Versionado semántico del software y changelog actualizado.
- `BLUEPRINT.md` actualizado en su Sección 3 con todos los Slices implementados.

### 5. Flujo Git y CI
- Protección de rama principal.
- CI pipeline con al menos compilación y tests automáticos.

### 6. Respaldo y Recuperación (Disaster Recovery)
- Mecanismo de backup automatizado para los datastores del sistema.
- Runbook de restauración documentado y probado.

### 7. Seguridad OWASP Top 10 Ampliada
- Control de acceso roto (RBAC validado, prevención de IDOR).
- Cabeceras de seguridad HTTP (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`).
- Cookies con flags `HttpOnly`, `SameSite` y `Secure`.

### 8. Documentación Operativa
- `README.md` autocontenido que permita a un desarrollador levantar el sistema en un comando.
- ADRs vigentes documentando decisiones arquitectónicas clave.

---

## Fase 3 — Conversión de Brechas en Especificaciones (Sintaxis EARS)

Cada brecha calificada como `❌ Gap` se formaliza bajo el estándar EARS:

```text
GAP: [Categoría] — [Descripción concisa del fallo]
EVIDENCIA: [Ruta/archivo#LXX o comando con salida de error]
IMPACTO: [Riesgo operativo, seguridad o rendimiento]

EARS SPEC:
CUANDO [condición o trigger operativo],
EL SISTEMA DEBERÁ [comportamiento exigido según ARQ-01 u OWASP],
DE FORMA QUE [criterio de aceptación observable y verificable].
```

---

## Fase 4 — Plan de Remediación Priorizado

Los specs EARS generados se consolidan en un plan priorizado:
- **Prioridad P0 (Bloqueante de Release):** Vulnerabilidades de seguridad (SQL injection, XSS, secrets), bloqueos SQLite (falta de WAL/timeout), concatenación de HTML en backend o falta de evidencia terminal. El sistema NO puede lanzarse a producción con gaps P0.
- **Prioridad P1 (Mejora en Siguiente Ciclo):** Gaps de usabilidad secundarios, telemetría granular o refinamiento de documentación.

---

## Mapeo en el Pipeline Moderno q-agent v2.0

| Paso | Prompt en q-agent v2.0 | Rol en el Ciclo |
|---|---|---|
| P01 | `P01_auditoria_mab_pc.md` | Discovery & Audit inicial (Produce Blueprint y Constitution con ARQ-01) |
| P02 | `P02_context_engineering.md` | Ingeniería de Contexto y Gestión de Memoria |
| P03 | `P03_gate_metaorquestacion.md` | Selección dinámica de motor (Gentle-AI ODD vs q-agent Standalone) |
| P04 | `P04_odd_feature_log.md` | Apertura de Bitácora Única (BMAD User Stories + Tareas atómicas ~400 LOC) |
| P05 | `P05_vertical_slice_apply.md` | Construcción de Slices Verticales con Mínima Indirección e Higiene |
| P06 | `P06_terminal_evidence_gate.md` | Verificación terminal obligatoria antes de marcar tareas |
| P07 | `P07_hygiene_and_blueprint.md` | Linters deterministas (0 tokens si limpio) y consolidación en BLUEPRINT.md |
| P09 | `P09_compliance_audit.md` | Auditoría CAB-RP 2.0 pre-release y plan de remediación EARS |
