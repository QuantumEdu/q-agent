---
name: q:audit-readonly
description: "Trigger: /q-audit-readonly, /audit-readonly, auditar sin tocar, auditar repo read-only, inspeccion no mutante, audit integridad, revisar contratos ODD. Ejecuta auditorías técnicas exhaustivas de arquitectura (ARQ-01), bitácoras ODD, UAC, integridad de frontend y superficie de APIs sin modificar ningún byte en disco."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-09-16"
---

# q:audit-readonly v2.0 (Inspección No Mutante ODD & ARQ-01)

## Goal
Ejecutar auditorías técnicas profundas y exhaustivas sobre repositorios brownfield o código recién implementado con la garantía absoluta de **cero mutaciones en disco**, evaluando el cumplimiento del **Artículo Constitucional ARQ-01**, bitácoras ODD (`q-tasks/*.md` u `odd/tasks/*.md`), criterios UAC, higiene de código y seguridad de APIs.

## When to Use
- Al iniciar el trabajo en un repositorio desconocido para hacer context grounding sin alterar Git.
- Cuando el usuario solicita auditar tareas, contratos o la UI expresando explícitamente "sin modificar archivos" o "modo lectura".
- Para certificar que las tareas marcadas como completadas `[x]` en la bitácora viva cuentan con evidencia real en `Terminal Evidence Gate`.

---

## Invariantes Operativos No Negociables
1. **Inmutabilidad Absoluta en Disco:** Prohibido terminantemente el uso de herramientas de edición (`replace_file_content`, `write_to_file`, `sed`, `git checkout .`). Al finalizar, `git status -s` debe ser idéntico al estado inicial (salvo el reporte generado si se solicitó explícitamente).
2. **CodeGraph Primero:** Si `codegraph` o MCPs están disponibles, usarlos prioritariamente para resolver llamadas y blast radius antes de búsquedas ciegas de texto.
3. **Tolerancia Cero a Falsas Completitudes (Anti-Mocking):** Verificar que ninguna tarea terminada dependa de datos simulados, stubs estáticos o formularios con valores hardcodeados para simular persistencia. Toda simulación no autorizada se clasifica como `❌ Gap P0`.

---

## Protocolo de Auditoría Paso a Paso

### Paso 1: Verificación de Entorno y Topología
1. Registrar el estado inicial del repositorio (`git status -s`).
2. Mapear la arquitectura contra el **Artículo ARQ-01**:
   - ¿Aplica Vertical Slices por defecto?
   - ¿Respeta el umbral de dominio rico (>15 reglas de negocio)?
   - ¿Cumple la persistencia pragmática (SQLite con WAL y busy_timeout)?
   - ¿Cumple la higiene de plantillas (cero HTML concatenado en strings de código)?

### Paso 2: Auditoría de Bitácora ODD y Criterios UAC
1. Inspeccionar la bitácora activa (`q-tasks/*.md` u `odd/tasks/*.md`).
2. Para cada tarea marcada como completada `[x]`:
   - Validar que exista una entrada correspondiente en la tabla `Terminal Evidence Gate`.
   - Comprobar que el comando registrado retornó exit code 0 y verificó el Criterio de Aceptación (`UAC`).

### Paso 3: Inspección de UI, Seguridad y APIs
1. **Seguridad SQL:** Verificar que el 100% de las consultas a BD utilicen sentencias preparadas (cero concatenaciones de strings en SQL).
2. **Higiene XSS:** Verificar que el renderizado de datos dinámicos use escape contextual automático.
3. **Manejo de Errores:** Comprobar que los handlers no devuelvan stack traces en producción ni errores 500 no controlados.

### Paso 4: Emisión del Reporte de Auditoría
Generar un informe en Markdown estructurado en:
- **Veredicto General:** [APTO PARA RELEASE / NO APTO / GAPS PENDIENTES].
- **Cumplimiento Constitucional (ARQ-01):** Tabla de verificación de las 6 cláusulas.
- **Hallazgos Críticos (P0):** Discrepancias de seguridad, falta de evidencia terminal o SQL injections.
- **Hallazgos Medios (P1):** Gaps de usabilidad, falta de tests de integración o documentación desactualizada.
- **Plan de Remediación:** Lista ordenada de tareas para subsanar los hallazgos en el siguiente ciclo.

---

## 🤖 Modo Especial: Revisión Agentiva de PR (Post-Build)
> **Trigger:** "revisar PR", "audit post-build", "code review agentivo de diff"

Cuando el objetivo sea auditar un Pull Request o diff antes de la revisión humana:
1. **Inputs:** `git diff main..HEAD`, `odd/tasks/<feature>.md` (o `q-tasks/`), y `CONSTITUTION.md`.
2. **Verificación de Diff:**
   - ¿El código añadido responde estrictamente a los criterios UAC de la bitácora?
   - ¿Se introdujeron anti-patterns o capas pasamanos prohibidas por ARQ-01?
   - ¿Hay tests unitarios/integración con datos reales para las nuevas rutas?
3. **Reporte Pre-Human Review:** Generar un análisis resumido con:
   - `[APPROVE]` / `[REQUEST_CHANGES]` sugerido para el revisor humano.
   - Puntos de atención crítica donde el ojo humano debe poner foco.
   - Declaración de límites: lo que el agente NO puede juzgar (ej. decisiones de negocio no escritas).
