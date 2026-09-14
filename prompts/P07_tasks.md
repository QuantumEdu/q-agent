---
id: P7_TASKS
titulo: "Desglose de Tareas Ejecutables con TDD — /tasks"
cuando_usar: "Para crear el checklist paso a paso que guiará la implementación."
prerequisitos: "design.md y specs/ aprobados."
entregables: "openspec/changes/{{CHANGE_ID}}/tasks.md"
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P7 — Desglose de Tareas Ejecutables con TDD
> `/tasks`

---

Actúa como Líder Técnico de Desarrollo.

Contexto:
Basado en `design.md` y `specs/{{FEATURE}}.md`, genera el plan de tareas ejecutable en `openspec/changes/{{CHANGE_ID}}/tasks.md`.

Reglas de Estructuración Obligatorias:
1. **Orden estricto por capas arquitectónicas**:
   `DOMINIO` → `INFRAESTRUCTURA / PERSISTENCIA` → `APLICACIÓN` → `API / CONTROLADORES` → `FRONTEND / CLIENTE`.
2. **Estructura atómica por tarea**: Cada tarea debe contener exactamente:
   - Checkbox de estado `[ ]`.
   - Etiqueta de alcance: `[CORE]` para tareas indispensables o `[OPTIONAL:DISABLED]` / `[OPTIONAL:ENABLED]` para tareas opcionales estilo Kiro.
   - Etiqueta `[TDD]` si el test se escribe ANTES del código de producción (obligatorio en reglas de dominio y lógica crítica).
   - Ruta exacta del archivo a crear o modificar (`Target:`).
   - **Comando exacto de verificación ejecutable** (`Verification:`).
3. **Determinismo**: El agente ejecutor NO puede marcar la casilla `[X]` sin haber corrido el comando de verificación y comprobado salida en verde (código de salida 0).
4. **Límite de granularidad**: Máximo 15 tareas por fase (unidades de trabajo cohesivas, no micro-pasos triviales).
5. **Compuerta de Tareas Opcionales (Patrón Kiro)**:
   - El arquitecto/usuario puede revisar `tasks.md` antes de invocar `/apply`.
   - Las tareas marcadas con `[OPTIONAL:DISABLED]` son ignoradas por el ejecutor en `/apply`.
   - Si el usuario desea incluir una tarea opcional, únicamente cambia el tag a `[OPTIONAL:ENABLED]`.

Formato de Plantilla Obligatorio:

```markdown
### Capa 1: Dominio Puro
- [ ] 1.1. [CORE] [TDD] Tests unitarios de invariantes y entidades de dominio
  - Target: `path/to/domain/entity_test.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/domain/...`
- [ ] 1.2. [CORE] Implementación de entidades puras e interfaces de puertos
  - Target: `path/to/domain/entity.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/domain/...`

### Capa 2: Infraestructura y Persistencia
- [ ] 2.1. [CORE] [TDD] Tests de integración para repositorio y snapshot de backup
  - Target: `path/to/infra/repository_test.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/infra/...`
- [ ] 2.2. [CORE] Implementación de adaptador de base de datos, DDL y migraciones
  - Target: `path/to/infra/repository.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/infra/...`

### Capa 3: Servicios de Aplicación y Casos de Uso
- [ ] 3.1. [CORE] [TDD] Tests de orquestación de caso de uso con mocks de puertos
  - Target: `path/to/app/usecase_test.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/app/...`
- [ ] 3.2. [CORE] Implementación de orquestador de caso de uso y emisión de telemetría
  - Target: `path/to/app/usecase.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/app/...`

### Capa 4: API, Rutas y Transporte
- [ ] 4.1. [CORE] Handlers de endpoints, validación de DTOs y mapeo de errores HTTP/gRPC
  - Target: `path/to/api/routes.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/api/...`

### Capa 5: Frontend / Cliente y Verificación Global
- [ ] 5.1. [CORE] Componente UI / Vista cliente y enlace con endpoints (si aplica)
  - Target: `path/to/client/...`
  - Verification: `{{FRONTEND_TEST_OR_BUILD_CMD}}`
- [ ] 5.2. [CORE] Suite completa de regresión y verificación contra escenarios BDD de specs/
  - Target: `openspec/changes/{{CHANGE_ID}}/verify-report.md`
  - Verification: `{{FULL_TEST_SUITE_CMD}}`

### Tareas Opcionales y Mejoras Adicionales (Estilo Kiro — Habilitables por el usuario)
- [ ] 6.1. [OPTIONAL:DISABLED] Generación de exportador alternativo (ej: CSV / JSON dump)
  - Target: `path/to/app/exporters.ext`
  - Verification: `{{TEST_RUNNER_CMD}} path/to/app/...`
- [ ] 6.2. [OPTIONAL:DISABLED] Benchmark de latencia / carga concurrente
  - Target: `tests/perf/benchmark.ext`
  - Verification: `{{PERF_TEST_CMD}}`
```

---

### Guía de Comandos de Verificación por Perfil de Stack:

Al generar `tasks.md`, sustituye las variables de verificación por los comandos exactos del stack del proyecto:

| Perfil | Stack | Test Unitario (`{{TEST_RUNNER_CMD}}`) | Verificación Global (`{{FULL_TEST_SUITE_CMD}}`) | Frontend/Build (`{{FRONTEND_CMD}}`) |
|---|---|---|---|---|
| **Perfil A** | **Go** | `go test -v -run TestNombre ./path/...` | `go test -v -race ./... && golangci-lint run` | `go build -v ./cmd/...` |
| **Perfil B** | **Python / FastAPI** | `pytest -v tests/path/test_item.py` | `pytest -v && ruff check . && mypy .` | `ruff check . && ruff format --check .` |
| **Perfil C** | **TypeScript / Bun / Node** | `bun test test/path/item.test.ts` | `bun test && tsc --noEmit && eslint .` | `bun run build` o `npm run build` |
| **Perfil D** | **Universal / Genérico** | `{{CMD_TEST_SINGLE}}` | `{{CMD_TESTS}} && {{CMD_TYPECHECK}} && {{CMD_LINT}}` | `{{CMD_BUILD}}` |

