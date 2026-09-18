---
id: P10_OPS_TO_ODD
titulo: "Puente de Incidentes de Operación a ODD — /ops-bridge"
cuando_usar: "Cuando un error en producción, reporte de usuario o alerta de monitoreo (Sentry/Datadog/Logs) requiere corrección."
prerequisitos: "Stack trace, logs o condiciones de falla observables provistas por el operador o webhook."
entregables: "Bitácora ODD estructurada en odd/tasks/ (Motor A) o q-tasks/ (Motor B) con Test RED obligatorio."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P10 — Puente de Telemetría e Incidentes a ODD (Ops to ODD)
> `/ops-bridge`

Actúa como Ingeniero de Confiabilidad de Sitio (SRE) y Desarrollador Senior de q-agent.

## Misión:
Tomar un reporte o incidente de runtime (cuyo contexto no existe en el código estático) y transformarlo deterministamente en una **Bitácora ODD de Corrección Quirúrgica**, protegiendo al agente de "adivinar" el problema mediante un test de reproducción obligatorio (*Reproduction-First*).

---

### PASO 1 — Captura y Normalización de Telemetría

El agente solicita o extrae los 5 vectores del incidente:
1. **Identificador del Incidente:** (Ej. `INC-2026-042` o slug de Sentry).
2. **Vertical Slice Afectada:** Identificar en `BLUEPRINT.md` qué slice es la dueña del fallo.
3. **Evidencia de Runtime:**
   - Stack trace completo.
   - Parámetros de entrada o payload que detonó la falla.
   - Mensaje de error exacto del motor (ej. `database locked`, `HTTP 500`, `null pointer`).
4. **Condiciones de Entorno / Carga:**
   - Concurrencia (¿ocurrió bajo múltiples peticiones simultáneas?).
   - Estado de la persistencia (¿bloqueo de SQLite WAL?).
5. **Impacto:** Severidad P0 (caída total), P1 (degradación parcial), P2 (cosmético).

---

### PASO 2 — Enrutamiento según Motor Dual

- **Si Motor A (Gentle-AI):**
  - Crear bitácora en: `odd/tasks/fix-{{INCIDENT_SLUG}}.md`.
  - Registrar observación en Engram: `mem_save(topic="odd/incidents/{{INCIDENT_SLUG}}", text="...")`.
- **Si Motor B (Standalone):**
  - Crear bitácora en: `q-tasks/fix-{{INCIDENT_SLUG}}.md`.
  - Toda la telemetría de runtime se inyecta directamente en el encabezado del archivo Markdown para no perderse al cerrar la terminal.

---

### PASO 3 — Generación de la Bitácora con Test de Reproducción Mandatorio

El archivo `odd/tasks/fix-...md` o `q-tasks/fix-...md` se estructura con:

```markdown
# TASK LOG ODD: Fix {{INCIDENT_ID}} — {{DESCRIPCION_CORTA}}
- **Severidad:** {{SEVERIDAD}} | **Slice:** {{VERTICAL_SLICE}}
- **Origen:** {{SENTRY_URL | LOGS | REPORTE_HUMANO}}

## 1. Evidencia de Runtime (Inyectada de Producción)
```text
{{STACK_TRACE_O_LOG_DE_ERROR}}
```
- **Condición Desencadenante:** {{CONDICION_EXACTA}}

## 2. Invariante Reproduction-First (Fase Roja Obligatoria)
> ⛔ REGLA DE BLOQUEO: Queda estrictamente prohibido tocar el código de implementación (`src/` o `internal/`) antes de que exista una prueba automatizada que reproduzca EXACTAMENTE este fallo y falle con código != 0.

- **Archivo de Test:** `features/{{SLICE}}/reproduction_test.go`
- **Comando de Verificación:** `go test -v -run TestReproduce_{{INCIDENT_ID}} ./features/{{SLICE}}`
- **Estado Inicial Esperado:** [RED_FAIL] (El test falla confirmando el bug).

## 3. Tareas Atómicas de Corrección (Fast-Track / Plan F si ≤3 archivos)
- [ ] **TASK-01 [TDD]**: Escribir prueba unitaria/integración que reproduzca el incidente con los datos de runtime.
- [ ] **TASK-02 [FIX]**: Aplicar corrección mínima respetando ARQ-01 (sin romper WAL ni agregar capas pasamanos).
- [ ] **TASK-03 [VERIFY]**: Comprobar que la prueba pasa a [GREEN_PASS] y la suite completa pasa con 0 regresiones.

## 4. Terminal Evidence Gate
| Tarea | Comando Ejecutado | Exit Code | Salida Terminal | Estado |
|---|---|---|---|---|
| TASK-01 | `go test -v -run TestReproduce_...` | 1 | FAIL: Expected X but got Y | [RED_CONFIRMADO] |
| TASK-02 | `go test -v -run Test...` | 0 | PASS: TestReproduce_... (0.01s) | [GREEN_VERIFICADO] |
| TASK-03 | `go test ./...` | 0 | ALL TESTS PASS | [CERTIFICADO] |
```

---

### PASO 4 — Transición Directa a P05/P06

Una vez creada la bitácora:
1. Si el fix involucra ≤3 archivos sin cambio de esquema: Se canaliza por **Plan F (Fast-Track)**.
2. El agente pasa de inmediato a `P05_vertical_slice_apply.md` y `P06_terminal_evidence_gate.md`, resolviendo el incidente con evidencia auditable de punta a punta.
