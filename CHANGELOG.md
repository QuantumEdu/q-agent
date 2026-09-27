# Changelog

All notable changes to **q-agent** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [2.5.3] - 2026-09-27

### Added
- **Selective & Optional Context Retrieval (`references/context-retrieval.md` & `templates/q-agent.json`)**:
  - Local-first baseline architecture; external memory providers (`gbrain`, `engram`, `skillvault`) are strictly optional and disabled by default (`enabled: false`).
  - Aggregate retrieval budget ceilings (max 3 candidate results, max 6,000 chars, ~1,500 token estimate).
  - Strict scope boundaries distinguishing public web research, general-reference libraries, and private-project memory.
- **Human-Scoped Execution Authority (`references/execution-authority.md`)**:
  - Formal operation taxonomy (`local-read`, `public-research`, `local-write`, `private-read`, `external-write`, `remote-execute`, `deploy`, `merge`).
  - Elimination of redundant onboarding loops: established project context and human decisions are reused across phases rather than replayed.
  - Prohibition of intrusive credential probing (`gh auth status` removed from general onboarding).
- **SkillVault Explorer in q-cockpit (`tools/q-cockpit/ui/index.html`)**:
  - Web UI tab with real-time search, markdown preview modal, copy-to-clipboard button, and disabled alert banner governed by `.q-agent.json`.
- **Zero-Dependency Native Python Terminal TUI (`tools/q-cockpit/q_cockpit_tui.py`)**:
  - Pure standard library Python terminal interface with 4 interactive views (Dashboard, Tasks Kanban, Git Commits & Diff, SkillVault) and `just cockpit-tui` recipe.
- **Context Retrieval & TUI Test Suites**:
  - 45 unit tests passing across skill integrity, context retrieval guardrails, scanner security, and tools execution.

---

## [2.5.2] - 2026-09-26

### Added
- **Bilingual Language Selector in q-cockpit (`tools/q-cockpit/ui/index.html`)**: Instant UI toggle `[ES | EN]` with 113 mirrored translation keys across all tabs, modals, gates, Kanban boards, and diff view without page reload; persisted in `localStorage`.
- **Conversational Language Mirroring Protocol (`SKILL.md`)**: Formalized bilingual rule directing the agent to automatically mirror the user's language (English for English prompts, Spanish for Spanish prompts) while keeping technical artifacts in English.
- **Interactive Mermaid Pan & Zoom Viewport (`tools/q-cockpit/q_cockpit.py`)**: Zero-dependency interactive viewport featuring Zoom In/Out (`+`/`-`), Real Size (`1:1`), Fit Width (`↔`), Fullscreen modal (`⛶`), Drag-to-Pan, Ctrl+Wheel zoom, and elimination of Mermaid's destructive proportional shrinking.

---

## [2.5.1] - 2026-09-26

### Added
- **Cockpit Authenticity Upgrades (`tools/q-cockpit`)**:
  - **Elimination of Fake Mock Fallback Tasks**: Elimination of fake mock fallback tasks (`q-agent-pipeline`); authentic empty list returned when repository is idle.
  - **Dynamic Pipeline Phase Pills**: Dynamic pipeline phase pills replacing static HTML mocks (`⚪ Proyecto en Reposo` indicator when idle).
  - **Authentic Idle State in Kanban Board**: Displays repository's recent Git commits (hash, author, message, relative date), working tree cleanliness, and quick action hints.
  - **Real Project Artifacts Explorer**: Dedicated drawer & tab scanning and rendering real project documents (`CONSTITUTION.md`, `README.md`, `SKILL.md`, `CHANGELOG.md`, `odd/tasks/*.md`, `audit/*.md`, `references/audit-manifest.yml`) with click-to-preview modal.
  - **Inferred Visual Diagrams in Socratic Grill**: Automatic discovery of embedded Mermaid diagrams in project Markdown files rendered live with Mermaid.js in dark theme, or structural architecture blueprint when no diagram is present.
  - **Enriched Header**: Version badge (`v2.5.1`), latest Git commit SHA, branch with status dot, and operational state indicator (`⚪ EN REPOSO (IDLE)` vs `🟢 ACTIVO`).

---

## [2.5.0] - 2026-09-26

### Added
- **Deterministic Technical Contracts Audit Gate (`scripts/audit_api_contracts.js`, `tools/q-audit-validator/validate_audit.py --mode technical`, `just audit-contracts`)**:
  - Zero-dependency deterministic audit gate evaluating technical project contracts:
    - **Disaster Recovery (A17)**: Detection of contingency runbooks, backup scripts, healthchecks (`/health`, `/healthz`, `/ping`, or Dockerfile `HEALTHCHECK`), and rollback/resilience capabilities.
    - **GitHub & CI Integrity (A03)**: Verification of `.gitignore`, CI workflows (`.github/workflows/`), triggers (`push`, `pull_request`), automated test/lint gates, and dependency automation configuration (`dependabot.yml` or Renovate).
    - **Observability & Telemetry (A14)**: Verification of structured logging libraries (`winston`, `pino`, `loguru`), APM instrumentation, and request correlation / tracing middleware (`x-request-id` / `correlation_id`).
    - **API Contracts Catalog (A06)**: Detection of OpenAPI/Swagger specifications (`openapi.yaml`, `swagger.json`) and route definitions or controller catalogs.
  - Dual implementation: zero-dependency Node.js script (`scripts/audit_api_contracts.js`) and unified Python CLI (`tools/q-audit-validator/validate_audit.py --mode technical`) with human-readable and `--json` reporting.
  - Fast-path recipe `just audit-contracts` added to `justfile` for immediate developer execution and CI verification.
- **q-cockpit v2 UI Enhancements (`tools/q-cockpit`)**:
  - **Code & Live Diff Tab**: Native live diff viewer with syntax highlighting, per-file addition/deletion stats, and contextual navigation.
  - **Terminal Evidence Details Modal**: Deep inspection modal displaying executed commands, exit codes, raw stdout/stderr logs, and timestamps.
  - **Dynamic Slice LOC Budget Counter**: Real-time ~400 LOC vertical slice budget counter with visual threshold indicators to prevent bloat and maintain atomic commit discipline.
  - **Dark Mode Custom Dialogs**: Fully styled, accessible modal dialogs with seamless dark theme integration.
- **Context-Isolated Adversarial Review Gate (`skills/q-adversarial-review`, `prompts/P06_terminal_evidence_gate.md`)**:
  - Implementation of context-isolated adversarial review gate (P06 Phase B in `SKILL.md`) inspired by Shopify Helix to eliminate confirmation bias.
  - Clean-context subagent dispatch auditing `git diff` against Constitutional Article ARQ-01 and UAC criteria before task completion.
  - Double-gate validation: Phase A (Empirical machine verification with exit code 0) + Phase B (Context-isolated binding adversarial review).
  - Formal registration of `q-adversarial-review` in `skill.json` and verification in `tests/test_skill_integrity.py`.

### Changed
- **Vertical Slices & Wave Execution Alignment**:
  - Clean separation from external framework coupling, standardizing vertical slice delivery with atomic commits (~400 LOC).
  - Constitutional Article ARQ-01 alignment across task log templates and orchestrator prompts for safe, concurrent wave execution.

### Security
- **Security Hardening & Dependency Governance in q-cockpit**:
  - Path traversal hardening in `q_cockpit.py` using canonical path resolution (`Path.resolve()`) rejecting any escape outside root directory.
  - CORS security hardening restricting cross-origin requests strictly to trusted local origins (`localhost`, `127.0.0.1`) with explicit `OPTIONS` preflight handling.
  - Automated dependency update governance configured via GitHub Dependabot (`.github/dependabot.yml`) for `github-actions` and `npm`.

---

## [2.4.0] - 2026-09-21

### Added
- **Parallel Audit Waves en Manifiesto y Orquestación (`references/audit-manifest.yml`, `SKILL.md` y `references/plans.md`)**:
  - Agrupación formal de los 17 ejes forenses en 4 Olas Temáticas Paralelas más 1 Ola Estratégica:
    - **Wave 1: Seguridad & Secretos** (`A02`, `A09`, `A10`, `A11`): Escaneo perimetral sin efectos colaterales (fugas de credenciales, inyecciones SQL/XSS, middleware auth/JWT y vectores SSRF).
    - **Wave 2: Arquitectura, Capas & Contratos** (`A01`, `A06`, `A13`, `A16`): Límites estructurales, separación Clean/Hexagonal, catálogo de endpoints REST/OpenAPI, límites de complejidad LOC y aislamiento multi-tenant.
    - **Wave 3: DevOps, Calidad & Confiabilidad** (`A03`, `A04`, `A05`, `A12`, `A14`, `A17`): Gates en pipelines CI/CD, infraestructura de tests, typos y errores 500 en hot paths, drift de dependencias, observabilidad/logs estructurados y planes de contingencia (DR).
    - **Wave 4: Frontend, Diseño & Accesibilidad** (`A07`, `A08`, `A15`): Cumplimiento de tokens del design system, accesibilidad WCAG 2.1 AA (aria/focus traps en modales) y auditoría de render/Web Vitals.
    - **Wave 5: Evolución Estratégica MAB-PC** (`E01`–`E05`): Latencia asíncrona, UX ergonomía, capacidades de dominio core, benchmark de mercado e innovaciones no contempladas.
- **Protocolo de Aislamiento de Contexto y Despacho Concurrente**:
  - Mecanismo de despacho paralelo vía subagentes especializados (`invoke_subagent`) o llamadas atómicas aisladas en lote, garantizando que cada subagente solo inspeccione sus `scope_patterns` asignados.
  - Eliminación del fenómeno *Lost in the Middle* y de la degradación por saturación de la ventana de contexto durante auditorías profundas.
- **Soporte de Waves y Prefijo `[AE]` en Herramientas de Auditoría**:
  - `tools/q-audit-validator/validate_audit.py`: Extracción de campo `wave` y soporte unificado de IDs `[AE]\d+` en el fallback parser sin dependencias.
  - `tools/q-audit-aggregator/generate_report.py`: Inclusión de atributos de wave en la ingesta del manifiesto canónico.
- **Suite de Pruebas de Integridad Ampliada (`tests/test_skill_integrity.py`)**:
  - Verificación estricta de versión `2.4.0` en `skill.json` y `SKILL.md`.
  - Validación del bloque `waves:` en `audit-manifest.yml`, existencia de los 17 ítems `A01`–`A17`, asignación válida de `wave: 1|2|3|4` y mapeo de `E01`–`E05` a `wave: 5`.

---

## [2.3.0] - 2026-09-21

### Added
- **Wave-Based Task Execution en Bitácora ODD (`templates/task-log-template.md` & `prompts/P04_odd_feature_log.md` / `P05_vertical_slice_apply.md`)**:
  - Descomposición topológica de tareas en Oleadas (Waves) para permitir ejecución concurrente/paralela de tareas independientes (Wave 1: contratos, esquemas, tests rojos; Wave 2: servicios y casos de uso; Wave 3: UI, endpoints, integración).
  - Soporte de columna `Wave` en la compuerta mecánica de `Terminal Evidence Gate`.
- **Plantilla Quirúrgica de Bugfix con Invariantes (`templates/bugfix-template.md`)**:
  - Estructura formal de 3 dimensiones para resolución de defectos en Plan F: Defecto Observado (con log real), Target EARS (`WHEN ... THE SYSTEM SHALL ...`), e Invariantes Inalterados para prevenir regresiones colaterales.
  - Vínculo formal en `references/plans.md` (Plan F Fast-Track).
- **Modos de Inclusión Condicional de Steering (`references/context-budgeting.md`)**:
  - Documentación y formalización de frontmatter YAML: `inclusion: always`, `inclusion: fileMatch` (`fileMatchPattern`) e `inclusion: manual` para poda inteligente de contexto y ahorro de tokens.
- **Visual Cockpit Wave Badges & ODD Scan (`tools/q-cockpit/ui/index.html` & `q_cockpit.py`)**:
  - Detección automática y renderizado de insignias estilizadas `🌊 Wave X` en las tarjetas Kanban del cockpit visual.
  - Escaneo automático de bitácoras vivas en carpetas `q-tasks/` y `odd/tasks/`.
- **Guardrails Declarativos en Configuración (`templates/q-agent.json` & `q_checklist.py`)**:
  - Bloque `guardrails` con listas permitidas y denegadas para escritura en filesystem (`fs_write_allowed`, `fs_write_denied`) y comandos de shell protegidos (`shell_denied`).
- **Suite de Pruebas de Integridad Ampliada (`tests/test_skill_integrity.py`)**:
  - Tests unitarios para validar la existencia y estructura de `bugfix-template.md`, el soporte de Waves en `task-log-template.md` y la sección de `guardrails`.

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
