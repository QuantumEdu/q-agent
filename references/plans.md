# Mapeo de flujo SDD por plan

Todas las rutas son relativas a la raíz de este paquete (`q-agent-v01/`).
Estructura de artefactos estándar: los cambios se alojan bajo `openspec/changes/{{CHANGE_ID}}/` (o en la raíz del repo para archivos globales como `CONSTITUTION.md` y `BLUEPRINT.md`).

---

## Plan A — Greenfield (sistema nuevo desde cero)

Ejecutar en orden estricto:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P0 | `templates/CONSTITUTION.md` | `CONSTITUTION.md` (reglas base + tabla ADRs) | `main` / `develop` |
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` (viabilidad y hexagonal ligera) | `develop` |
| P4 | `prompts/P04_propose.md` | `openspec/changes/{{CHANGE_ID}}/proposal.md` | `develop` |
| P5 | `prompts/P05_spec.md` | `openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `openspec/changes/{{CHANGE_ID}}/design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `openspec/changes/{{CHANGE_ID}}/tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | Código verificado + `verify-report.md` | `feature/<name>` |
| P1.5 / P04b | `prompts/P04b_constitution_sync.md` | `CONSTITUTION.md` (sync drift + log) | `develop` |

> P0 inicializa la Constitution antes de entrar al pipeline.
> P1 MAB-PC y P3 Evolución no aplican en Plan A (no hay código preexistente).

**Gate obligatorio:** después de P4 `/propose` — mostrar al usuario y esperar aprobación explícita.

---

## Plan B — Brownfield (feature / evolución sobre código existente)

Ejecutar en orden:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P1 | `prompts/P01_auditoria_mab_pc.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `develop` |
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` | `develop` |
| P3 | `prompts/P03_evolucion_blueprint.md` | `BLUEPRINT_V2.md` + `DIFF_V1_VS_V2.md` | `develop` |
| P4 | `prompts/P04_propose.md` | `openspec/changes/{{CHANGE_ID}}/proposal.md` | `feature/<name>` |
| P5 | `prompts/P05_spec.md` | `openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `openspec/changes/{{CHANGE_ID}}/design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `openspec/changes/{{CHANGE_ID}}/tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | Código verificado + `verify-report.md` | `feature/<name>` |
| P1.5 / P04b | `prompts/P04b_constitution_sync.md` | `CONSTITUTION.md` (sync drift + log) | `develop` |

**Gate obligatorio:** después de P4 `/propose`.

**Bifurcación Fast-Track (Nivel 1):** Si P4 clasifica el requerimiento como Nivel 1 (≤3 archivos, sin impacto en Dominio ni BD), deriva directamente a **P8 en modo Fast-Track** (test unitario + fix quirúrgico + commit atómico), saltando P5, P6 y P7.

**Etiquetas MAB-PC (P1):**
- `[OBSERVADO]` — comprobado en código real
- `[INFERIDO]` — deducido por convención
- `[CONFLICTO]` — contradicción entre fuentes; pasa a gate humano

---

## Plan C — Audit (revisar, auditar y diagnosticar)

Ejecutar en orden:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P1 | `prompts/P01_auditoria_mab_pc.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `audit/<date>` |
| P9 (CAB-RP) | `prompts/P09_compliance_audit.md` | `AUDIT_REPORT.md` (matriz + specs EARS + plan P0/P1) | `audit/<date>` |
| Remediación | Generación de Issues GitHub | Issues creados por brecha con severidad | `audit/<date>` |

**No hay gate de scope ni implementación de código en Plan C.** El ciclo concluye con la entrega de `AUDIT_REPORT.md` y la creación de los Issues de remediación en GitHub.

**Invariantes de Auditoría P9:**
- Inmutabilidad absoluta en disco (`git status -s` idéntico al estado de partida).
- CodeGraph primero para análisis de dependencias y blast radius.
- Anti-Mock / Fake Data check: tolerancia cero a funcionalidades simuladas con stubs.

---

## Templates Canónicos

| Plantilla | Archivo |
|-----------|---------|
| Architecture Decision Record | `templates/ADR.md` |
| Blueprint del Sistema | `templates/BLUEPRINT.md` |
| Constitución Arquitectónica | `templates/CONSTITUTION.md` |
| Propuesta de Cambio (/propose) | `templates/PROPOSAL.md` |

---

## Modos de Interacción y Compuertas (Human-in-the-Loop)

El agente puede operar en tres modalidades de interacción, configurables en `.q-agent.json` o solicitadas explícitamente en el prompt de invocación:

1. **`autonomous` (Totalmente Autónomo):**
   - El agente ejecuta todas las fases de inicio a fin sin detenerse a consultar al usuario.
   - Ideal para ejecuciones desatendidas, CI/CD o pipelines automatizados.

2. **`supervised` (Supervisado por Compuertas - RECOMENDADO):**
   - El agente avanza de forma continua pero **se detiene obligatoriamente** en compuertas de decisión arquitectónica críticas (`interactive_gates`):
     - **Gate P03 (Evolución/ADR):** valida decisiones de diseño antes de escribir especificaciones.
     - **Gate P04 (Propuesta/Scope):** valida el alcance y clasificación de calibre (Full SDD vs Fast-Track).
     - **Gate P09 (Compliance/Release):** solicita autorización antes de integrar ramas a `main`/`develop`.
   - En cada compuerta, el agente formula una pregunta estructurada (usando la herramienta interactiva de preguntas del runtime, ej. `ask_question`) y espera respuesta antes de avanzar.

3. **`interactive` (Paso a Paso / Didáctico):**
   - El agente se detiene en **cada una de las fases** (P01 hasta P09) presentando el resumen de lo realizado y preguntando confirmación para el siguiente paso.
   - Ideal para sesiones de pair programming o revisión detallada.

---

## Protocolo de Aislamiento de Workspace (Git Worktrees)

Para evitar colisiones con el IDE del desarrollador o interferir con cambios de rama en caliente, el agente soporta aislamiento mediante **Git Worktrees**:

1. **Creación del Worktree Hermano:**
   En lugar de alterar el directorio de trabajo activo con `git checkout -b <branch>`, el agente crea un worktree en una carpeta hermana:
   ```bash
   git worktree add ../{{REPO_NAME}}-worktrees/{{CHANGE_ID}} -b {{BRANCH_NAME}} {{BASE_BRANCH}}
   ```
   Registra en el flight recorder:
   `[STEP-04] [WORKTREE] [CREATED] Isolated worktree at ../{{REPO_NAME}}-worktrees/{{CHANGE_ID}}`
2. **Ejecución Aislada:**
   Toda la implementación, ejecución de linters y tests ocurre dentro de la ruta del worktree.
3. **Integración y Limpieza:**
   Una vez completada la fase P08/P09 y realizado el merge a la rama base, el worktree se elimina de forma limpia:
   ```bash
   git worktree remove ../{{REPO_NAME}}-worktrees/{{CHANGE_ID}}
   ```
   Registra:
   `[STEP-07] [WORKTREE] [REMOVED] Worktree ../{{REPO_NAME}}-worktrees/{{CHANGE_ID}} cleaned up`

---

## Protocolo Reproduction-First (Fase Roja Obligatoria — SWE-agent Pattern)

Tanto en Fast-Track (Nivel 1) como en tareas TDD de Full SDD:
1. **Regla de Oro:** Queda terminantemente prohibido editar o crear archivos de implementación en `src/` sin haber ejecutado primero un test en `tests/` que falle de forma reproducible.
2. **Registro Obligatorio en Flight Recorder:**
   - Test fallando (Red): `[STEP-06] [REPRODUCTION] [RED_FAIL] <test_name> failed: <reason>`
   - Test pasando (Green): `[STEP-06] [REPRODUCTION] [GREEN_PASS] <test_name> passed`
3. **Límite de Recuperación:** Máximo 3 intentos de corrección. Al tercer fallo, se ejecuta un rollback atómico (`git checkout -- <archivos>`), registrando `[ROLLBACK] [EXECUTED]`.

---

## Protocolo de Poda de Contexto (Context Budgeting via AST)

Para mantener el consumo de tokens bajo control y preservar la capacidad de razonamiento del LLM en repositorios de mediano y gran porte:
1. Durante P01, P02, P03 y P06, priorizar la extracción de **esqueletos AST** (firmas de funciones, interfaces y tipos) sobre la lectura de archivos completos.
2. Leer archivos completos con cuerpo de métodos únicamente al implementar la tarea específica en P08.
3. Referencia detallada: `references/context-budgeting.md`.

---

## Nota de compatibilidad con ejecutores

El flujo es tool-agnostic por diseño. El executor (Codex / Antigravity / OpenCode / Pi) recibe los artefactos generados bajo `openspec/changes/{{CHANGE_ID}}/` como contexto de entrada delimitado sin dependencias propietarias.

