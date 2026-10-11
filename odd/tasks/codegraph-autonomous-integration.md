# Feature: Integración Autónoma de CodeGraph en q-agent

- **Feature:** `codegraph-autonomous-integration`
- **Objective:** Incorporar CodeGraph como política arquitectónica de primer orden en q-agent (Hard Ordering Rule, Lazy-Init autónoma, Dual Surface MCP/CLI e Impact Gates para blast radius) tanto en Motor Gentle-AI como en Motor q-agent Standalone.
- **Why:** Reemplazar exploraciones de texto ciegas (`grep`/`find` loops) por consultas de grafo de AST estructuradas en milisegundos, reduciendo el consumo de contexto un 80-90% y formalizando el cálculo de impacto previo a cada Vertical Slice.
- **Scope:**
  - Definición de política estricta y contrato de superficie dual (MCP `codegraph_explore` + CLI nativo) en `references/dual-engine.md` y `references/context-budgeting.md`.
  - Contrato de auto-inicialización (`codegraph init -y <root>`) e impact analysis en `prompts/` (`P01`, `P04`, `P09`) y `SKILL.md`.
  - Actualización de `skills/q-audit-readonly/SKILL.md` preservando presupuesto <= 200 líneas.
  - Suite de pruebas de regresión e integridad en `tests/test_skill_integrity.py`.
- **Constraints:**
  - Preservar presupuesto <= 200 líneas en todos los archivos `SKILL.md`.
  - Compatibilidad total con runtimes sin MCP mediante fallback transparente al CLI upstream `codegraph`.
  - Cero dependencias externas pesadas adicionales.
- **Effective TDD Mode:** disabled (ordinary functional checks and deterministic test assertions).

## Tasks

- [x] **TASK-01: Contrato Central de CodeGraph en Dual Engine y Context Budgeting**
  - Documentar Hard Ordering Rule, Lazy-Init autónoma y Dual Surface (MCP + CLI) en `references/dual-engine.md`.
  - Incorporar niveles de grafo e impacto en `references/context-budgeting.md`.
  - Actualizar `SKILL.md` raíz manteniendo límite estricto de 200 líneas.
  - *Route:* direct inline | *Evidence:* commit `b066205` | *Checks:* línea budget 117/200, suite intacta.

- [x] **TASK-02: Auto-Inicialización e Impact Gates en Prompts y Sub-Skills**
  - Incorporar verificación y bootstrap (`test -d .codegraph || codegraph init -y`) en `prompts/P01_auditoria_mab_pc.md`, `prompts/P04_odd_feature_log.md` y `prompts/P09_compliance_audit.md`.
  - Actualizar `skills/q-audit-readonly/SKILL.md` con el protocolo de fallback a CLI.
  - *Route:* direct inline | *Evidence:* commit `acb28b6` | *Checks:* línea budget 44/200, contratos sincronizados.

- [x] **TASK-03: Verificación con Pruebas Automatizadas y Cierre**
  - Añadir aserciones en `tests/test_skill_integrity.py` para validar los contratos de CodeGraph (auto-init, MCP y CLI fallback).
  - Ejecutar suite completa `python3 -m unittest discover tests`.
  - Registrar evidencia y cerrar bitácora ODD.
  - *Route:* direct inline | *Evidence:* 72/72 tests en verde (1.215s) | *Checks:* suite 100% pasando.
