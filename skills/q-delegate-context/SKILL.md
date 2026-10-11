---
name: q-delegate-context
description: "Coordina lectura de archivos, boilerplate e implementación acotada mediante subagentes del mismo entorno o ejecutores externos como Codex y Antigravity. Selecciona ejecutor, modelo y esfuerzo de forma automática o explícita, y valida resultados."
license: Apache-2.0
metadata:
  version: "2.0.0"
  context_policy: "PROGRESSIVE"
  requires: ["references/execution-authority.md"]
  may_call: ["references/external-cli-adapters.md"]
  produces: ["Delegation Task Brief", "Execution Report"]
---

# q-delegate-context v2.0 — Delegación Agnóstica de Contexto y Código

## 1. Quick Bootstrap & Triggers
- **Propósito**: Mantener al agente principal como coordinador de alto nivel y delegar tareas delimitadas para optimizar ventana de contexto, tokens, tiempo o especialización técnica.
- **Cuándo Aplica**:
  - Lecturas extensas o análisis de varios archivos para evitar saturar el contexto principal.
  - Generación de boilerplate determinista (DTOs, fixtures, esquemas, configuraciones repetitivas).
  - Tareas concurrentes o desacopladas que se beneficien de subagentes nativos o CLIs externas (`codex`, `agy`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO delegar decisiones de arquitectura o reglas de negocio**: El coordinador retiene el juicio central.
  - ⛔ **PROHIBIDO delegar tareas microscópicas**: No subagentizar búsquedas simples que se resuelven con `grep`/`view_file` (el costo de coordinación superaría el beneficio).
  - No delegar seguridad, autenticación o diagnósticos ambiguos de raíz a ejecutores no especializados.
- **Política de Contexto**: `PROGRESSIVE`. Cargar `references/external-cli-adapters.md` únicamente si se despacha vía CLI externa (`codex` o `agy`).

## 2. Taxonomía de Delegación
Separar estrictamente cuatro conceptos:
1. **Coordinador**: Mantiene el objetivo del ciclo y valida/acepta los resultados finales.
2. **Ejecutor**: Subagente nativo del harness (`invoke_subagent`) o herramienta externa CLI (`codex`, `agy`).
3. **Modelo**: LLM asignado al ejecutor (ej. flash, pro, sonnet).
4. **Esfuerzo**: Nivel de razonamiento (low, medium, high) soportado por la plataforma.

## 3. Prioridad de Selección de Ruta
1. **Elección explícita del usuario**: Respetar instrucciones tipo *"Usa codex para esto"* o *"No delegues"*.
2. **Subagentes nativos del entorno**: Ruta preferida por defecto (`invoke_subagent`) por menor sobrecarga.
3. **Ejecutores externos vía CLI**: Solo cuando el usuario lo solicite o aporte una ventaja sustancial comprobada.

## 4. Contrato de Ejecución Paso a Paso
- [ ] **M1 (Preparación del Brief)**: Redactar un brief autónomo con:
  - Objetivo claro y preguntas concretas.
  - Contexto mínimo indispensable y rutas de archivos permitidas para lectura/escritura.
  - Criterios de aceptación y verificaciones obligatorias.
  - ⛔ Restricciones: Prohibido relanzar otros agentes o ampliar el alcance sin permiso.
- [ ] **M2 (Aislamiento de Concurrencia)**: Si implica escrituras en paralelo, aislar en Git Worktree (`python3 tools/q-worktree/q_worktree.py create`). Prohibidas escrituras simultáneas en el mismo checkout.
- [ ] **M3 (Despacho)**:
  - **Vía Nativa**: Invocar `invoke_subagent` con rol, prompt acotado y modelo/esfuerzo resueltos.
  - **Vía CLI Externa**: Cargar `references/external-cli-adapters.md`, invocar con sandbox apropiado y timeout estricto (180s lectura / 900s código).
- [ ] **M4 (Contrato de Respuesta del Ejecutor)**:
  Exigir reporte con: `status` (`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`), `summary`, `changed_files`, `evidence` y `checks`.
- [ ] **M5 (Validación y Aceptación por el Coordinador)**:
  - Para lecturas: Verificar hechos críticos directamente antes de tomar decisiones.
  - Para código: Inspeccionar `git diff`, revisar que no haya archivos no autorizados y ejecutar tests locales.
  - ⛔ **Nunca aceptar solo por `exit 0` o un `DONE` no verificado empíricamente.**

## 5. Completion Gate
Antes de incorporar el resultado al flujo principal:
- [ ] Evidencia de ejecución inspeccionada por el coordinador (diff real o citas de archivo:línea).
- [ ] Máximo 2 rondas de corrección si el ejecutor comete fallos.
- [ ] Estado final declarado formalmente:
  - `[COMPLETE]` ──► Trabajo aceptado y verificado por el coordinador.
  - `[BLOCKED - reason]` ──► El ejecutor reportó bloqueo o faltante de contexto.
  - `[FAILED - reason]` ──► Se agotó el límite de correcciones o hubo timeout.