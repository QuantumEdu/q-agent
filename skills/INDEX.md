# Índice y Catálogo Canónico de Skills de q-agent

> **Propósito:** Catálogo central de descubrimiento, ruteo y gobernanza de skills para el orquestador y subagentes. Permite identificar en un solo vistazo el propósito, disparadores, anti-patrones de activación, política de contexto y contratos de entrada/salida sin necesidad de cargar los archivos `SKILL.md` individuales.

---

## Matriz de Ruteo y Descubrimiento

| Skill | Propósito | Cuándo Invocar (Triggers) | Cuándo NO Invocar (Anti-Triggers) | Política Contexto | Dependencias (requires / may_call / produces) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[`q-agent`](../SKILL.md)** | Orquestador maestro de ciclo ODD, Dual Engine y Vertical Slices. | Inicio de proyecto, nueva feature, brownfield, fast-track, auditoría pre-release. | Tareas triviales de un solo archivo, lectura pura sin ciclo. | `PROGRESSIVE` | **requires**: `execution-authority.md`, `CONSTITUTION.md`<br>**may_call**: todas las child skills<br>**produces**: `odd/tasks/*.md`, `BLUEPRINT.md`, `REVIEW.md` |
| **[`q:adversarial-review`](q-adversarial-review/SKILL.md)** | Auditoría implacable en subagente aislado con memoria de hallazgos persistentes. | En Paso 6 tras tests de máquina, cierre de slice (~400 LOC), re-revisión tras rebote. | ⛔ Edición de código, ejecución en el mismo hilo del escritor, sin diff para auditar. | `FULL` | **requires**: `CONSTITUTION.md`, `git diff`<br>**may_call**: ninguna (subagente aislado)<br>**produces**: Veredicto `APPROVED`/`REJECTED`, Matriz `R-IDs` |
| **[`q:audit-readonly`](q-audit-readonly/SKILL.md)** | Inspección técnica exhaustiva de arquitectura, UAC y APIs con cero mutaciones. | Grounding en repositorios desconocidos, auditorías solicitadas como "solo lectura". | ⛔ Modificar código, aplicar fixes, parches en caliente o resolver CI. | `PROGRESSIVE` | **requires**: `CONSTITUTION.md`, repo en limpio<br>**may_call**: `tools/q-audit-validator`<br>**produces**: Reporte de auditoría de solo lectura |
| **[`q:ci-fixer`](q-ci-fixer/SKILL.md)** | Reparación quirúrgica de fallos en pipelines de CI/CD sin relajar contratos. | Build de GitHub Actions roto, linters o análisis de tipos con fallos, coverage gate fail. | ⛔ Debilitar contratos (`# noqa`, bajar cobertura), refactorizaciones fuera de alcance. | `COMPACT` | **requires**: Logs de fallo de CI o test roto<br>**may_call**: `uv run ruff`, `pnpm eslint`<br>**produces**: Parche quirúrgico con exit code 0 |
| **[`q-delegate-context`](q-delegate-context/SKILL.md)** | Coordinación de lectura pesada, boilerplate y ejecución mediante subagentes o CLIs externas. | Lecturas de múltiples archivos, generación de DTOs/boilerplate, trabajo desacoplado. | ⛔ Delegar arquitectura central, decisiones de producto o micro-tareas simples. | `PROGRESSIVE` | **requires**: `execution-authority.md`<br>**may_call**: `external-cli-adapters.md`, `q-worktree`<br>**produces**: Task Brief, Execution Report |
| **[`q:deliberate`](q-deliberate/SKILL.md)** | Debate dialéctico multi-agente (Proponente, Adversario, Sintetizador) para arquitectura. | En Paso 2a ante decisiones técnicas complejas, diseño de sistemas, disyuntivas reales. | ⛔ Decisiones ya acordadas, tareas mecánicas, preguntas con respuesta en código. | `PROGRESSIVE` | **requires**: `execution-authority.md`<br>**may_call**: `prompts/proponent.md`, `adversary.md`, `synthesizer.md`<br>**produces**: ADRs en `docs/adr/`, `CONTEXT.md` |
| **[`q:gbrain-assistant`](q-gbrain-assistant/SKILL.md)** | Gateway especializado a GBrain para búsquedas semánticas híbridas y memoria. | Búsqueda contextual de historial, persistencia de hechos atómicos, diagnóstico vectorial. | ⛔ Consultar Engram o SkillVault (stores independientes), escrituras desde pedidos read-only. | `PROGRESSIVE` | **requires**: `context-retrieval.md`<br>**may_call**: `templates/gbrain-prompts.md`<br>**produces**: Síntesis de consulta, hechos en grafo |
| **[`q-grill-me`](q-grill-me/SKILL.md)** | Entrevista socrática implacable (1 pregunta por turno) para estresar alcance y supuestos. | En Paso 2c en proyectos Greenfield (Plan A) o ideas ambiguas antes de redactar specs. | ⛔ Múltiples preguntas a la vez, tareas brownfield con alcance ya delimitado. | `COMPACT` | **requires**: Idea inicial de proyecto<br>**may_call**: `tools/q-cockpit`<br>**produces**: Scope & Invariants Brief |
| **[`q:session-wrap`](q-session-wrap/SKILL.md)** | Cierre estructurado de sesión de desarrollo con persistencia local-first. | Final de sesión, pausa de jornada, comando `/session-wrap` o `/wrap`. | ⛔ Asumir completitud si falló la persistencia en disco, inventar commits ajenos. | `COMPACT` | **requires**: `context-retrieval.md`, git status<br>**may_call**: herramientas locales de backup<br>**produces**: Local Session Summary, bitácora cerrada |

---

## Convenciones de Políticas de Contexto

- **`COMPACT`**: Archivo autosuficiente de tamaño mínimo (<60 líneas). Se lee completo en un solo turno sin referencias externas pesadas.
- **`PROGRESSIVE`**: Bootstrap conciso (<100 líneas). Carga sus sub-directorios (`workflows/`, `references/`, `templates/`) únicamente si la rama condicional de la tarea lo exige.
- **`FULL`**: Archivo crítico con matrices de evaluación exhaustivas. Debe leerse completamente antes de emitir cualquier dictamen o veredicto vinculante.
