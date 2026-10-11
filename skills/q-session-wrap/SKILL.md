---
name: q:session-wrap
description: "Trigger: /q-session-wrap, /session-wrap, /wrap, cerrar sesion. Local-first session summary with optional authorized external persistence and backup."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-10-10"
  context_policy: "COMPACT"
  requires: ["references/context-retrieval.md"]
  may_call: ["Local backup tools"]
  produces: ["Local Session Summary", "Closed Task Document"]
---

# q:session-wrap v2.0 — Cierre de Sesión Local-First

## 1. Quick Bootstrap & Triggers
- **Propósito**: Concluir una sesión de desarrollo con progreso comprobado, estado de recuperación limpio y bitácora actualizada en el repositorio local.
- **Cuándo Aplica**:
  - Al finalizar una jornada o pausa de desarrollo.
  - Al completar un ciclo completo de `q-agent` (Paso 7 o Paso 8).
  - Bajo invocación explícita (`/session-wrap`, `/wrap`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO asumir éxito si la persistencia en disco falla**: No omitir errores de escritura local.
  - No reclamar commits o cambios no realizados en la sesión actual como trabajo propio.
  - No ejecutar respaldos o escrituras remotas sin autorización explícita previa.
- **Política de Contexto**: `COMPACT`. No requiere productos de base de datos ni servicios externos para operar.

## 2. Contrato de Ejecución Paso a Paso
- [ ] **M1 (Inspección de Estado)**: Comprobar `git status -s`, commits realizados y evidencia terminal de tests.
- [ ] **M2 (Persistencia Local-First)**: Guardar el resumen en la bitácora activa (`q-tasks/*.md` u `odd/tasks/*.md`) con: Objetivo, Instrucciones, Hallazgos, Completado, Próximos Pasos y Archivos.
- [ ] **C1 [Condicional: Escritura Externa]**: Solo si está configurado y autorizado, sincronizar copia en store externo.
- [ ] **C2 [Condicional: Backup SQLite]**: Solo con origen y destino autorizados expresamente, ejecutar respaldo SQLite.
- [ ] **M3 (Reporte Final en Chat)**: Presentar el resumen visible al usuario con rutas de archivos locales y enlaces.

## 3. Completion Gate
Antes de declarar la sesión como cerrada:
- [ ] Resumen escrito exitosamente en el archivo local de tareas en disco.
- [ ] Cada operación reportada con estado unificado:
  - `[COMPLETE]` ──► Resumen local persistido y comprobado.
  - `[N/A - reason]` ──► Stores externos o backups no requeridos ni configurados.
  - `[BLOCKED - reason]` ──► Fallo de permisos de escritura en disco local.
