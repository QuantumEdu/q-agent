# Feature: Skills Hardening, Modularization & Execution Contracts

- **Feature Name**: `skills-hardening-and-contracts`
- **Objective**: Harden and modularize q-agent skills under the 200-line budget standard, implementing explicit execution contracts (mandatory/conditional/optional), strict completion gates, anti-triggers ("When NOT to use"), progressive context loading, and a central skills discovery catalog.
- **Why**: Eliminate context bloat (lost in the middle), avoid accidental mutations, ensure hard gates are never truncated, and provide deterministic execution and discovery.
- **Scope**:
  - `SKILL.md` (root): Streamline orchestrator to <200 lines, extract Plan C audit protocol to `workflows/plan-c-audit.md`.
  - `skills/q-adversarial-review/SKILL.md`: Add strict Completion Gate with R-IDs matrix validation, anti-triggers, and `context_policy: FULL`.
  - `skills/q-audit-readonly/SKILL.md`: Add anti-triggers and clean-tree completion gate verification (`git status -s`).
  - `skills/q-delegate-context/SKILL.md`: Modularize to <200 lines, extract external CLI runners to `references/external-cli-adapters.md`.
  - `skills/q-gbrain-assistant/SKILL.md`: Streamline to <100 lines, extract prompt catalog to `templates/gbrain-prompts.md`.
  - `skills/q-deliberate/SKILL.md` & `skills/q-ci-fixer/SKILL.md`: Standardize with anti-triggers, execution contracts, and limits.
  - `skills/INDEX.md`: Central discovery catalog table with policies, triggers, and dependencies.
  - `skills/q-session-wrap/SKILL.md` & `skills/q-grill-me/SKILL.md`: Standardize with unified taxonomies.
  - `tests/test_skill_integrity.py`: Verify all tests and line-budget integrity.
- **Constraints**:
  - Maximum 200 lines per `SKILL.md` (hard ceiling).
  - 100% backward compatibility with q-agent tools, prompt references, and test suite.
  - Zero external dependencies.
- **Mirror Status**: Pending (Engram mirror `odd/skills-hardening-and-contracts/tasks`).

---

## Tasks

- [x] **TASK-01**: Reestructurar `SKILL.md` (<200 líneas) y extraer protocolo Plan C a `workflows/plan-c-audit.md`.
  - Route: Delegated / writer
  - Checks: Line count down to 116 lines (<200), 69/69 unit tests passing.
  - Evidence: `workflows/plan-c-audit.md` created; `SKILL.md` reduced from 337 to 116 lines; all 69 unit tests pass.

- [x] **TASK-02**: Blindar `skills/q-adversarial-review/SKILL.md` con Completion Gate estricto, anti-triggers y política `FULL`.
  - Route: Delegated / writer
  - Checks: Line count down to 79 lines (<200), Completion Gate y anti-triggers presentes.
  - Evidence: Review Remembers con matriz R-IDs estricta y bloqueo de cierre con veredicto REJECTED.

- [x] **TASK-03**: Cerrar compuerta en `skills/q-audit-readonly/SKILL.md` con anti-triggers y verificación de no-mutación.
  - Route: Delegated / writer
  - Checks: Line count down to 44 lines (<200), zero-mutation gate verificado con git status.
  - Evidence: Anti-triggers explícitos (cero edición de código) y Completion Gate de árbol limpio.

- [x] **TASK-04**: Modularizar `skills/q-delegate-context/SKILL.md` (<200 líneas) extrayendo adaptadores a `references/external-cli-adapters.md`.
  - Route: Delegated / writer
  - Checks: Line count down to 62 lines (<200), adaptadores extraídos cleanly.
  - Evidence: `references/external-cli-adapters.md` creado; `SKILL.md` reducido de 412 a 62 líneas (85% menos tokens).

- [x] **TASK-05**: Aligerar `skills/q-gbrain-assistant/SKILL.md` (<100 líneas) moviendo catálogo de prompts a `templates/gbrain-prompts.md`.
  - Route: Delegated / writer
  - Checks: Line count down to 53 lines (<100), prompts extraídos a plantilla.
  - Evidence: `templates/gbrain-prompts.md` creado; bootstrap ligero de gateway a GBrain.

- [x] **TASK-06**: Normalizar `skills/q-deliberate/SKILL.md` y `skills/q-ci-fixer/SKILL.md` con anti-triggers y Completion Gates.
  - Route: Delegated / writer
  - Checks: `q-ci-fixer` (48 líneas) y `q-deliberate` (72 líneas) normalizadas con anti-triggers y gates.
  - Evidence: Ambas skills con checklists de ejecución, límites de pasadas y taxonomía unificada.

- [ ] **TASK-07**: Crear `skills/INDEX.md` con catálogo central de descubrimiento y dependencias; conectar `tools/q-checklist`.
  - Route: Delegated / writer
  - Checks: `skills/INDEX.md` exists and indexes all 8 child skills + root orchestrator.
  - Evidence: Pending

- [ ] **TASK-08**: Normalizar `skills/q-session-wrap/SKILL.md` y `skills/q-grill-me/SKILL.md`; verificar suite completa de tests de integridad.
  - Route: Delegated / writer
  - Checks: `python3 -m unittest discover tests` passing 100%.
  - Evidence: Pending
