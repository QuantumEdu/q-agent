---
id: P8_APPLY_VERIFY
titulo: "Implementación y Verificación Guiada por Constitución — /apply & /verify"
cuando_usar: "Para ejecutar el código real, verificar los tests y auditar contra los principios constitucionales."
prerequisitos: "tasks.md, design.md y specs/ aprobados."
entregables: "Código implementado + informe de verificación."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P8 — Implementación y Verificación Guiada por Constitución
> `/apply` + `/verify`

---

Actúa como Ingeniero de Software Senior (SDD Executor & Verifier).

Misión:
Implementa la Fase {{NUMERO_FASE}} de {{PROYECTO_NOMBRE}} según el calibre asignado:

---

### ENRUTAMIENTO POR CALIBRE:

#### RUTA 1: Modo Fast-Track (Nivel 1 — Micro-cambio / Patch / Fix)
* Si el requerimiento fue calificado como Nivel 1 (≤3 archivos, sin impacto en Dominio ni BD):
  1. **Invariante Reproduction-First (Fase Roja Obligatoria):** Escribe ÚNICAMENTE la prueba unitaria que reproduce el bug o define el comportamiento esperado (`tests/`). Queda estrictamente prohibido tocar `src/` en este paso.
  2. **Verificación de Falla:** Ejecuta la suite de pruebas localmente. Comprueba que el test falla (código de salida ≠ 0). Registra en `.q-agent/flight_recorder.log`:
     `[STEP-06] [REPRODUCTION] [RED_FAIL] <test_name> failed as expected: <reason>`
  3. **Implementación Quirúrgica (Fase Verde):** Escribe la solución mínima en `src/`.
  4. **Verificación de Éxito:** Ejecuta nuevamente la suite. Debe pasar al 100% (código 0). Registra en el log:
     `[STEP-06] [REPRODUCTION] [GREEN_PASS] <test_name> passed with 0 regression`
  5. Refactoriza y ejecuta la verificación del perfil de stack (Go, Python o TypeScript).
  6. Realiza un commit atómico con mensaje convencional (`fix: ...`, `style: ...`).
  7. *Fin del ciclo Fast-Track (no requiere verify-report.md ni P09).*

---

#### RUTA 2: Modo Full SDD (Nivel 2 — Feature / Módulo)
Sigue fielmente `tasks.md`, `design.md` y `specs/{{FEATURE}}.md` cumpliendo el ciclo de 2 fases:

### Fase A: Ejecución Tarea por Tarea (`/apply`)
1. **Iteración Secuencial Atómica**: Toma exactamente UNA tarea pendiente de `tasks.md` a la vez, en el orden de capas establecido (`DOMINIO` → `INFRA` → `APPLICACIÓN` → `API` → `UI`).
2. **Ciclo TDD Estricto & Reproduction-First**: Para tareas marcadas con `[TDD]`:
   - *Red*: Escribe la prueba en el archivo `Target` indicado. Ejecuta el comando `Verification` y comprueba que falla por la razón esperada. Registra `[STEP-06] [REPRODUCTION] [RED_FAIL]` en el flight recorder.
   - *Green*: Escribe la implementación mínima requerida. Ejecuta el comando `Verification` y comprueba que pasa (código 0). Registra `[STEP-06] [REPRODUCTION] [GREEN_PASS]`.
   - *Refactor*: Limpia el código eliminando duplicaciones y optimizando sin romper los tests.
3. **Límite de Recuperación y Rollback**: Si una tarea falla en la verificación y no se resuelve tras 3 intentos consecutivos:
   - Detén el ciclo inmediatamente.
   - Ejecuta rollback atómico del intento actual (`git checkout -- <archivos>`).
   - Registra en `.q-agent/flight_recorder.log`: `[STEP-06] [ROLLBACK] [EXECUTED] Task <task_id> aborted after 3 failed attempts`.
   - Notifica el bloqueo al usuario con diagnóstico exacto.
4. **Validación Inmediata**: No avances a la siguiente tarea hasta que el comando `Verification` de la tarea actual pase al 100%. Solo entonces marca `[X]` en `tasks.md`.

### Fase B: Quality Gates y Auditoría de Cierre (`/verify`)
Una vez completadas todas las tareas de `tasks.md`, ejecuta el protocolo de verificación global según el **Perfil de Stack** del proyecto:

| Perfil | Stack | Suite Completa & Concurrencia | Verificador Estático & Linting | Invariante de Aislamiento |
|---|---|---|---|---|
| **Perfil A** | **Go** | `go test -v -race ./...` | `go vet ./...` && `golangci-lint run` | `grep -rn "internal/web" internal/domain` == 0 |
| **Perfil B** | **Python / FastAPI** | `pytest -v --tb=short` | `mypy .` (o `pyright`) && `ruff check .` | Core puro sin imports de frameworks web ni DB |
| **Perfil C** | **TypeScript / Bun / Node** | `bun test` o `npm test` | `tsc --noEmit` (o `tsc -b`) && `eslint .` | Tipado estricto sin `any` ni bypasses de compilador |
| **Perfil D** | **Universal / Genérico** | `{{CMD_TESTS}}` | `{{CMD_TYPECHECK}}` && `{{CMD_LINT}}` | Suite completa con código de salida 0 |

1. **Trazabilidad BDD**: Valida que cada escenario `GIVEN / WHEN / THEN` de `specs/{{FEATURE}}.md` cuente con una prueba automatizada que lo respalde con evidencia observable.
2. **Sincronización Atómica de Versión (GitHub ↔ App)**:
   - Lee la versión en `VERSION` o manifiesto de paquetes (`package.json`, `pyproject.toml`, etc.).
   - Compara con el endpoint `/health` o badge de versión en la app.
   - Si difieren: reconcilia ambas fuentes en el mismo commit atómico y documenta el ajuste en `CHANGELOG.md`.

Entregable Formal: Genera `openspec/changes/{{CHANGE_ID}}/verify-report.md` con:
- Veredicto final: `PASS` / `FAIL`.
- Lista de tareas completadas y archivos modificados (con número de líneas).
- Resumen de ejecución de tests (cobertura y tiempo de corrida).
- Checklist de cumplimiento de principios constitucionales con evidencia `[OBSERVADO: ruta/línea]`.
- Estado de sincronización de versión GitHub ↔ App.
