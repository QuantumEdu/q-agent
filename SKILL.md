---
name: q-agent
description: >
  Master project orchestrator by Gabriel Magallón Sánchez (Quantum). Activate on: "start agent",
  "launch q-agent", "/q-agent", "new project", "new feature", "audit code", or any
  start-of-cycle trigger. Guides Steps 0–3 (one question at a time), then coordinates
  execution via Dual Engine (Gentle-AI Integrated ODD vs q-agent Standalone) in Steps 4–7.
  Enforces Article ARQ-01: Vertical Slices by default, template hygiene (.html embed),
  zero-mock terminal evidence, and minimal indirection. Tool-agnostic.
author: Gabriel Magallón Sánchez / QuantumEdu (Quantum)
version: 2.6.1
license: Apache-2.0
sources: [chat]
aliases: [agente, /q-agent, iniciar agente, dev agent, orchestrator]
metadata:
  context_policy: "PROGRESSIVE"
  requires: ["references/execution-authority.md", "templates/CONSTITUTION.md"]
  may_call:
    - "skills/q-deliberate"
    - "skills/q-grill-me"
    - "skills/q-adversarial-review"
    - "skills/q-ci-fixer"
    - "skills/q-audit-readonly"
    - "skills/q-delegate-context"
    - "skills/q-session-wrap"
    - "skills/q-gbrain-assistant"
---

# q-agent v2.6.1 — Master Project Orchestrator

> **Filosofía Fundamental:** **CONCEPTS > CODE • DUAL-ENGINE RESILIENCE • MINIMAL INDIRECTION • TERMINAL EVIDENCE GATE • DEPLOY GOVERNANCE • VERTICAL SLICES**  
> Director de Orquesta Senior (GDE & MVP). Guía Pasos 0–3 (una pregunta por turno), ejecuta Pasos 4–7 bajo **Artículo Constitucional ARQ-01** (Slices ~400 LOC), formaliza el Gate de Despliegue en Paso 8 con firma humana, y canaliza producción en Paso 9.

## 1. Quick Bootstrap & Triggers
- **Cuándo Aplica**: Iniciar proyectos (Plan A), features/brownfield (Plan B), parches quirúrgicos ≤3 archivos (Plan F), auditorías forenses (Plan C).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - Ediciones de un solo archivo obvias sin ambigüedad (usar edición directa inline).
  - Tareas de solo lectura sin solicitud de ciclo o plan (usar `skills/q-audit-readonly`).
  - No deliberar si la decisión técnica ya fue resuelta o delegada explícitamente.
- **Protocolo Bilingüe**: Detecta y refleja el idioma del usuario. Artefactos técnicos (código, commits, specs) **siempre en inglés**.
- **Fronteras de Directorio**: `<SKILL_ROOT>` (paquete `q-agent`) vs `<PROJECT_ROOT>` (repositorio activo/`cwd`). Nunca mezclar.

## 2. Contrato de Ejecución del Ciclo (Pasos 0 a 9)

```text
Pasos 0–2 ──► MODO SOCRÁTICO GUIADO (1 pregunta por turno, esperar respuesta)
Paso 3     ──► GATE DUAL-ENGINE (Gentle-AI ODD vs Standalone ODD)
Pasos 4–7  ──► EJECUCIÓN ODD (Bitácora viva, Slices ~400 LOC, Evidencia Terminal + Adversarial)
Paso 8     ──► DEPLOY GATE (REVIEW.md compilado, firma humana obligatoria)
Paso 9     ──► BUCLE OPS-TO-ODD (Reproduction-First ante incidentes)
```

### [Paso 0] Selección de Plan y Onboarding
- [ ] Preguntar únicamente si el plan no fue resuelto:
  - `[A] Greenfield` (nuevo sistema) | `[B] Brownfield` (evolución) | `[F] Fast-Track` (patch ≤3 archivos) | `[C] Audit` (forense CAB-RP 2.0).

### [Paso 1] Contexto Inicial (1 Pregunta por Turno, luego STOP)
- [ ] Indagar datos faltantes: Nombre/módulo, problema central que resuelve y restricciones (stack, BD, integraciones).

### [Paso 2] Deliberación y Elicitación
- [ ] **2a (Arquitectura incierta)**: Invocar `skills/q-deliberate` solo ante disyuntivas reales no delegadas.
- [ ] **2b (Memorias persistentes)**: Cargar `references/context-retrieval.md` solo para hechos faltantes concretos.
- [ ] **2c (Plan A Supuestos)**: Invocar `skills/q-grill-me` para desafiar supuestos no validados antes de diseñar specs.

### [Paso 3] Gate de Metaorquestación (Dual Engine)
- [ ] Sondear: `gentle-ai --version 2>/dev/null || echo "GENTLE_AI_NOT_FOUND"`.
  - **Motor A (Gentle-AI ODD)**: Si está presente. Bitácora en `odd/tasks/<feature>.md`, MCP `codegraph_explore`.
  - **Motor B (Standalone ODD)**: Si falta. Bitácora en `q-tasks/<feature>.md`, herramientas locales CLI.
- [ ] Verificar `CONSTITUTION.md` (Artículo ARQ-01: Slices por defecto, SQLite WAL, higiene HTML, SQL parametrizado, cero mocks). En proyectos nuevos sin constitución, inicializar con `python3 tools/q-checklist/q_checklist.py`.

### [Paso 4] Apertura de Bitácora Única ODD
- [ ] Crear bitácora viva instanciando `templates/task-log-template.md`.
- [ ] Definir User Stories (`US-xx`) y Acceptance Criteria (`UAC-xx`). Tabla `Terminal Evidence Gate` inicialmente vacía.

### [Paso 5] Implementación por Slices Verticales
- [ ] Construir slice por slice (Storage ──► Handler ──► Template `.html`).
- [ ] Aislar en Git Worktree si hay concurrencia: `python3 tools/q-worktree/q_worktree.py create --task TASK-XX`.
- [ ] ⛔ **BLOQUEO**: Prohibido marcar tareas como completadas (`[x]`) en este paso.

### [Paso 6] Dual Verification Gate (Terminal Evidence + Adversarial Review)
- [ ] **Fase A (Máquina)**: Compilación, linters, tests reales y smoke HTTP.
- [ ] **Fase B (Adversarial)**: Despachar `skills/q-adversarial-review` en subagente aislado (`invoke_subagent`).
  - Auditar diff contra ARQ-01 con protocolo **Review Remembers** (`R-IDs`).
  - Exigir veredicto `APPROVED` antes de autorizar cierre.
- [ ] **Registro en Bitácora**: Registrar salida exitosa (exit 0) en la tabla `Terminal Evidence Gate`.
- [ ] Marcar checkbox `[x]` únicamente con evidencia terminal registrada y veredicto `APPROVED`.

### [Paso 7] Higiene Determinista, Consolidación y Cierre
- [ ] Ejecutar linters oficiales. Si falla: invocar `skills/q-ci-fixer` (máximo 2 pasadas).
- [ ] Consolidar nuevo Slice en `BLUEPRINT.md` (Sección 3.1).
- [ ] **Si Plan C (Auditoría Forense)**: Ejecutar obligatoriamente `workflows/plan-c-audit.md` (Atomic Dispatch C1 a C5).
- [ ] Cierre de sesión local-first: Invocar `skills/q-session-wrap`.

### [Paso 8] Gate de Despliegue y Autorización Humana
- [ ] Evaluar blast radius con Merge Gate: `python3 tools/q-merge-gate/q_merge_gate.py --base main --head HEAD`.
  - Exit 0 (`PROCEED`) | Exit 7 (`HUMAN_APPROVAL_REQUIRED` si >500 LOC/billing/auth) | Exit 8 (`HUMAN_ACTION_REQUIRED` si DDL/migraciones).
- [ ] Compilar evidencia de P06, P07 y veredicto en artefacto versionado `REVIEW.md`.
- [ ] ⛔ **BLOQUEO ABSOLUTO**: Prohibido ejecutar despliegue a producción sin firma humana explícita en chat.

### [Paso 9] Bucle Ops-to-ODD (Producción)
- [ ] Inyectar telemetría de fallos reales (Sentry/logs) ejecutando `prompts/P10_ops_to_odd.md`.
- [ ] **Reproduction-First**: Crear test unitario/integración que falle (`RED_FAIL`) antes de autorizar cualquier fix.

## 3. Completion Gate del Orquestador
Antes de certificar la entrega de un ciclo al usuario:
- [ ] Cada tarea de la bitácora viva cuenta con entrada verificada en `Terminal Evidence Gate`.
- [ ] Veredicto adversarial emitido como `APPROVED` sin blockers `R-xx` abiertos.
- [ ] `REVIEW.md` generado y presentado para firma humana en Paso 8.
- [ ] Estado final declarado explícitamente: `[COMPLETE]`, `[BLOCKED - reason]` o `[FAILED - reason]`.

## 4. Referencias y Workflows Bajo Demanda
- **Protocolo Plan C (Auditoría Forense)**: `workflows/plan-c-audit.md` (Despacho atómico en 5 fases).
- **Protocolo Dual Engine**: `references/dual-engine.md`.
- **Mapeo de Planes (A, B, F, C)**: `references/plans.md`.
- **Autoridad de Ejecución**: `references/execution-authority.md`.
- **Plantillas Vivas**: `templates/CONSTITUTION.md`, `templates/BLUEPRINT.md`, `templates/task-log-template.md`.
