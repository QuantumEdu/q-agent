# Changelog

All notable changes to **q-agent** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.2.2] - 2026-09-19

### Added
- **GitHub Actions CI Pipeline (`.github/workflows/ci.yml`)**: Validación automática continua en GitHub (Python 3.10, 3.11, 3.12) para compilación de sintaxis (`py_compile`), suite de pruebas unitarias, verificación de esquemas (`skill.json`) y smoke tests de CLI.
- **Suite de Pruebas Automatizadas (`tests/`)**:
  - `test_skill_integrity.py`: Verificación de `skill.json`, frontmatter YAML de `SKILL.md` y `references/audit-manifest.yml`.
  - `test_tools_execution.py`: Compilación y ejecución `--help` de todas las herramientas CLI en `tools/`.
  - `test_audit_validator.py`: Carga y validación determinista de manifiestos y reporte `AUDIT_GAPS.json`.
- **Taxonomía de GitHub Issue Labels**: Aprovisionamiento directo en GitHub de los 24 labels de `references/issue-labels.md` (`type:*`, `priority:*`, `status:*`, `scope:*`).
- **Guía de Contribución y Plantillas de Comunidad**:
  - `CONTRIBUTING.md`: Guía de contribución, estándares de calidad, principios ARQ-01, Zero-Mock evidence y flujo de ramas Git.
  - `.github/ISSUE_TEMPLATE/bug_report.md`: Plantilla con label `type:fix`.
  - `.github/ISSUE_TEMPLATE/feature_request.md`: Plantilla con label `type:feature`.
  - `.github/ISSUE_TEMPLATE/audit_finding.md`: Plantilla para hallazgos y `type:nfr-gap`.
  - `.github/ISSUE_TEMPLATE/adr.md`: Plantilla para Architecture Decision Records (`type:adr`).
  - `.github/pull_request_template.md`: Plantilla de PR con checklist de calidad y evidencia Zero-Mock obligatoria.

### Fixed
- **`tools/q-checklist/q_checklist.py`**: Añadido soporte explícito de `-h` y `--help` para salir limpiamente sin bloquear interactivamente la terminal en entornos desatendidos o CI.

---

## [2.2.1] - 2026-09-19

### Fixed
- **Specification Drift en SSOT (`SKILL.md` y `references/plans.md`)**: Se cerró la brecha entre las herramientas de Atomic Dispatch y las instrucciones operativas maestras que lee el LLM.
- **Infiltración Prematura de Plan F**: Prohibición explícita de mutar archivos de `src/`, `internal/` o `cmd/` durante Plan C. Queda vetado el modo mixto (Audit + Fix) hasta certificar la auditoría.
- **Prohibición de Informes Monolíticos por LLM**: Regla estricta contra la redacción manual de `AUDIT_REPORT.md` en el chat. *"Completeness is a filesystem property, not an LLM output property."*

### Added
- **Compuerta Mecánica de Validación Obligatoria (Fase C3)**: Cableado mandatorio de `python3 tools/q-audit-validator/validate_audit.py --mode manifest --level [0|1|2]` con salida Exit Code 0 obligatoria antes de interactuar con el usuario.
- **Agregación Determinista (Fase C4)**: Invocación obligatoria de `python3 tools/q-audit-aggregator/generate_report.py` para ensamblar deterministamente `AUDIT_REPORT.md`, `PLAN_DE_MEJORA.md`, `REMEDIATION_ISSUES.md` y `PROPUESTA_EVOLUTIVA.md` con cero consumo de tokens.
- **GitHub Agent Skills**: Asignación de topics oficiales (`agent-skill`, `agent-skills`, `skills`, `mcp`, `mcp-server`, `knowledge-base`, `ai-agents`, `sdd`, `tdd-framework`, `clean-architecture`, `llmops`) para indexación nativa por GitHub y registries agénticos.

---

## [2.2.0] - 2026-09-18

### Added
- **`q-cockpit` (Visual Socratic Grill & Mission Cockpit)**:
  - Servidor HTTP/REST nativo en Python (`tools/q-cockpit/q_cockpit.py`) con cero dependencias Node.js/npm.
  - Interfaz web interactiva SPA (`tools/q-cockpit/ui/index.html`) con mazo de tarjetas visuales para elicitación socrática y render en vivo de prototipos (`visual.html`) y diagramas Mermaid.
  - Tablero Kanban en tiempo real para tareas TDD (Backlog / In Progress Red-Green / Completed).
  - Semáforos de compuertas de calidad (Gates P03, P04, P08) con disparadores de aprobación/rechazo humano.
  - Comando global `q-cockpit` en `$PATH` y subcomando `q-agent cockpit`.

---

## [2.1.0] - 2026-09-17

### Added
- **Paso 8 — Deploy Gate (`prompts/P08_deploy_gate.md`)**:
  - Compilación formal de evidencias observables en `REVIEW.md`.
  - Regla de bloqueo absoluto: el agente tiene estrictamente prohibido realizar merges a `main` o deploys a producción sin firma humana explícita.
- **Paso 9 — Ops Bridge (`prompts/P10_ops_to_odd.md`)**:
  - Inyección de telemetría de producción (Sentry/Datadog/incidentes reales) hacia bitácoras ODD.
  - Protocolo Reproduction-First con creación mandatoria de test reproductor en rojo (`RED_FAIL`) previo a cualquier modificación de código.
- **Atribución Formal**:
  - Manifiesto de atribución [`ATTRIBUTION.md`](ATTRIBUTION.md) y firma de autoría de Gabriel Magallón Sánchez / QuantumEdu.
  - Adopción de licencia Apache 2.0.

---

## [2.0.0] - 2026-09-16

### Added
- **Arquitectura Dual Engine**:
  - Motor A: Gentle-AI Integrated ODD (para entornos con `gentle-ai` CLI, CodeGraph MCP y bitácoras `odd/tasks/*.md`).
  - Motor B: q-agent Standalone ODD (para servidores, CI/CD y entornos mínimos con bitácoras `q-tasks/*.md`).
- **Constitución Suprema y Artículo ARQ-01**:
  - Vertical Slices por defecto con mínima indirección.
  - Umbral de Dominio Rico (>15 reglas complejas) para justificar capas hexagonales.
  - Persistencia pragmática con SQLite WAL (busy_timeout ≥ 5000ms).
  - Higiene de plantillas: prohibición de cadenas HTML en backend; uso estricto de vistas `.html` empaquetadas (`//go:embed`, TSX, Jinja2).
  - Ciberseguridad mandatoria: 100% SQL parametrizado y escape contextual anti-XSS.
- **Terminal Evidence Gate (P06)**:
  - Verificación empírica en terminal con registro obligatorio de comando, código de salida 0 y salida observable antes de tachar tareas a `[x]`.
- **Protocolo Atomic Dispatch para Plan C**:
  - Manifiesto atómico [`references/audit-manifest.yml`](references/audit-manifest.yml) con 17 ítems de cumplimiento (`A01`–`A17`) y 5 ítems de evolución estratégica MAB-PC (`E01`–`E05`).
  - Validador determinista `validate_audit.py` y agregador multirreporte `generate_report.py`.
- **Herramienta `q-checklist`**:
  - Matriz interactiva de decisiones pre-vuelo en terminal (`tools/q-checklist/q_checklist.py`).

---

## [1.0.0] - 2026-09-13

### Added
- Lanzamiento inicial del paquete hermético `q-agent-v01`.
- Definición de los 3 Planes fundamentales: Plan A (Greenfield), Plan B (Brownfield), Plan C (Audit).
- Skills auxiliares integradas: `q-deliberate`, `q-grill-me`, `q-ci-fixer`, `q-delegate-context`, `q-gbrain-assistant`, `q-session-wrap`.
- Aislamiento mediante Git Worktrees (`../{repo}-worktrees/`).
- Protocolo de poda de contexto mediante esqueletos AST.
