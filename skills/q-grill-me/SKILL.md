---
name: q-grill-me
description: "A relentless, structured interview to stress-test and sharpen a project plan, scope, or architecture before building. Challenges assumptions, forces clarity on trade-offs, and extracts non-negotiables."
sources: [chat]
aliases: [grill-me, /grill-me, interview, elicitation]
license: Apache-2.0
metadata:
  version: "2.0.0"
  context_policy: "COMPACT"
  requires: ["Project idea or ambiguous plan"]
  may_call: ["tools/q-cockpit"]
  produces: ["Scope & Invariants Brief"]
---

# q-grill-me v2.0 — Elicitación Socrática de Alcance y Supuestos

## 1. Quick Bootstrap & Triggers
- **Propósito**: Realizar una entrevista de alta precisión para destapar puntos ciegos, supuestos no validados y ambigüedades de alcance ANTES de escribir código.
- **Cuándo Aplica**:
  - En Paso 2c de `q-agent` (especialmente Plan A Greenfield).
  - Al recibir una idea ambigua o requerimiento difuso.
  - Bajo demanda explícita (`/grill-me`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO hacer más de una pregunta por turno**: Una sola pregunta filosa por mensaje; esperar siempre respuesta antes de continuar.
  - No usar en tareas con alcance ya delimitado, cerrado o mecánicamente especificado.
  - No aceptar respuestas vagas ("debe ser rápido", "seguridad estándar") sin repreguntar con métricas.
- **Política de Contexto**: `COMPACT`. No requiere referencias externas.

## 2. Contrato de Ejecución (5 Dimensiones Críticas)
Interrogar de 3 a 5 rondas afiladas sobre:
- [ ] **M1 (Límites de Alcance - The Knife)**: Qué queda explícitamente EXCLUIDO del MVP.
- [ ] **M2 (Modos de Fallo - The 3 AM Test)**: Peor escenario de fallo y qué degrada vs qué crashea.
- [ ] **M3 (Datos e Invariantes)**: Fuente única de la verdad y datos que jamás pueden corromperse.
- [ ] **M4 (Usuarios y Concurrencia)**: Actores reales y volumen de escrituras concurrentes.
- [ ] **M5 (Restricciones Operativas)**: Infraestructura, presupuesto y regulaciones.

## 3. Modo Visual Opcional (`q-cockpit`)
Si se prefiere interfaz gráfica web en lugar de chat terminal:
`python3 tools/q-cockpit/q_cockpit.py serve`

## 4. Completion Gate
Antes de devolver el control al orquestador:
- [ ] Síntesis estructurada entregada: **Scope & Invariants Brief**.
- [ ] Estado final:
  - `[COMPLETE]` ──► 3–5 rondas concluidas y brief cristalizado en chat.
  - `[BLOCKED - reason]` ──► El usuario interrumpió o no pudo definir las restricciones mínimas.
