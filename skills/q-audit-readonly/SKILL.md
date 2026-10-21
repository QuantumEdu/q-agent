---
name: q:audit-readonly
description: "Trigger: /q-audit-readonly, /audit-readonly, auditar sin tocar, auditar repo read-only, inspeccion no mutante, audit integridad, revisar contratos ODD. Ejecuta auditorías técnicas exhaustivas de arquitectura (ARQ-01), bitácoras ODD, UAC, integridad de frontend y superficie de APIs sin modificar ningún byte en disco."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.1.0"
  date: "2026-10-10"
  context_policy: "PROGRESSIVE"
  requires: ["CONSTITUTION.md"]
  produces: ["Read-Only Audit Report"]
---

# q:audit-readonly v2.1 — Inspección No Mutante ODD & ARQ-01

## 1. Quick Bootstrap & Triggers
- **Propósito**: Ejecutar auditorías técnicas profundas sobre código brownfield o recién implementado con garantía absoluta de **cero mutaciones en disco**, evaluando cumplimiento de **Artículo ARQ-01**, bitácoras ODD, criterios UAC, seguridad e higiene.
- **Cuándo Aplica**:
  - Context grounding en repos desconocidos sin alterar Git.
  - Inspección de tareas, contratos o UI cuando el usuario pide "solo lectura" o "sin modificar archivos".
  - Verificación de que tareas marcadas con `[x]` en bitácoras vivas tengan evidencia terminal real.
  - Revisión pre-merge / PR review agentivo.
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO modificar código o aplicar fixes**: Cero uso de `replace_file_content`, `write_to_file`, `git checkout .`, `sed` o scripts mutantes.
  - No usar para resolver fallos de CI (usar `skills/q-ci-fixer`).
  - No usar para implementar features o parches en caliente (usar `q-agent` Plan B o Plan F).
- **Política de Contexto**: `PROGRESSIVE`. Iniciar con análisis estructural; profundizar en archivos específicos bajo demanda.

## 2. Invariantes Operativos No Negociables
1. **Inmutabilidad Absoluta en Disco**: Al finalizar, `git status -s` debe ser idéntico al estado inicial (salvo el reporte generado si fue solicitado expresamente).
2. **CodeGraph / Dual Surface Primero**: Verificar índice (`test -d .codegraph || codegraph init -y`). Resolver llamadas, dependencias y blast radius vía `codegraph_explore` (MCP) o `codegraph` CLI antes de búsquedas ciegas de texto.
3. **Tolerancia Cero a Mocks (Anti-Mocking)**: Ninguna tarea finalizada puede depender de datos simulados o stubs no autorizados (clasificado como `❌ Gap P0`).
4. **Citación Explícita de Claves Primarias**: Toda evidencia extraída de tablas de base de datos o incidencias debe citar obligatoriamente la clave primaria formal (`<tabla>.<pk> = <id>`) además de los campos semánticos.

## 3. Contrato de Ejecución Paso a Paso
- [ ] **M1 (Topología y ARQ-01)**: Registrar estado inicial (`git status -s`). Evaluar Vertical Slices, persistencia SQLite WAL y ausencia de HTML en backend.
- [ ] **M2 (Bitácora ODD & UAC)**: Validar que cada tarea completada `[x]` tenga evidencia de exit code 0 en `Terminal Evidence Gate`.
- [ ] **M3 (Seguridad & APIs)**: Comprobar 100% SQL parametrizado, escape contextual anti-XSS y ausencia de errores 500 no controlados.
- [ ] **M4 (Emisión de Reporte)**: Generar reporte estructurado: Veredicto, Matriz ARQ-01, Gaps P0/P1 y Plan de Remediación.

## 4. Completion Gate
Antes de declarar concluida la auditoría:
- [ ] Comprobar estado de disco: `git status -s` **sin cambios no autorizados** respecto al inicio.
- [ ] Reporte emitido con veredicto claro: `[APTO PARA RELEASE]`, `[NO APTO]` o `[GAPS PENDIENTES]`.
- [ ] Taxonomía de gate registrada: `[COMPLETE]` (si árbol limpio y reporte emitido), `[BLOCKED - reason]` (si se detectó mutación accidental).
