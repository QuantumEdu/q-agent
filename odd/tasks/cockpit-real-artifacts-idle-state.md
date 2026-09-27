# Feature: Cockpit Real Artifacts & Idle State (No Fake Mocks)

- **Feature Name**: `cockpit-real-artifacts-idle-state`
- **Objective**: Transform `q-cockpit` from hardcoded static mockups to an authentic, deterministic engineering dashboard. Remove fake pipeline tasks, display real project artifacts, render inferred Mermaid diagrams from project documentation when no `visual.html` exists, and provide a rich "En Reposo (Idle)" view with the latest Git commits and metadata.
- **Why**: Cognitive dissonance and confusion occur when an idle project shows fake running phases and phantom tasks. A senior engineering cockpit must reflect ground truth at all times.
- **Scope**:
  - `tools/q-cockpit/q_cockpit.py`:
    - Remove hardcoded `q-agent-pipeline` fake tasks in `scan_tasks()`.
    - Enhance `scan_artifacts()` to discover `odd/tasks/*.md`, `audit/*.md`, `docs/`, `references/audit-manifest.yml`.
    - Enhance `/visual` and `/api/status` to detect and render Mermaid diagrams embedded in Markdown files (`README.md`, `docs/`, `odd/tasks/`) if no `visual.html` exists.
    - Expose project version, current commit SHA, and active/idle status in `/api/status`.
  - `tools/q-cockpit/ui/index.html`:
    - Dynamic pipeline phase pills (active phase when in session, neutral/idle pills with `IDLE` badge when stopped).
    - Real artifacts explorer drawer or card list with click-to-preview modal.
    - Idle state Kanban view showing latest Git commits, repository health, and next-step actions.
    - Navbar enriched with version `v2.5.0`, commit hash, absolute path tooltip, and branch.
  - `tests/test_tools_execution.py`:
    - Tests for real artifact scanning, empty tasks behavior (no fake items), and Mermaid/visual extraction.
- **Constraints**:
  - Zero external npm or Python dependencies.
  - Native Mermaid.js CDN or standalone client-side rendering for diagrams.
  - 100% test suite passing.
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Refactor `q_cockpit.py` to eliminate fake mock fallback tasks, enrich artifact scanning, add markdown Mermaid diagram discovery, and expose version/commit status.
  - Route: Delegated / writer
  - Checks: `scan_tasks()` returns empty list `[]` when no task files exist; `/api/status` includes version, commit, and enriched artifacts.
  - Evidence: Verified empty list return on empty projects. Added `get_project_version()`, `scan_artifacts()` discovering `odd/tasks`, `audit/`, `references/audit-manifest.yml`, `docs/`, and core governance files. Added markdown Mermaid scanner and live rendering in `serve_visual()`, with dark architecture blueprint fallback.

- [x] **TASK-02**: Update `ui/index.html` with dynamic pipeline rendering, authentic Idle State with latest commits in Kanban, Real Artifacts drawer/modal, and enriched navbar.
  - Route: Delegated / writer
  - Checks: UI displays real repository state, latest commits in idle mode, and artifacts without hardcoded mockups.
  - Evidence: Enriched navbar with version badge (`v2.5.0`), Git commit chip (`🔖 ...`), branch dot, and status badge (`🟢 ACTIVO` / `⚪ EN REPOSO (IDLE)`). Rendered pipeline dynamically based on active phase or neutral idle. Implemented Kanban idle container with recent commits and quick actions. Added dedicated Tab 4 Artifacts Explorer and Tab 2 Quick Artifacts panel with live preview and modal inspection.

- [x] **TASK-03**: Update unit tests in `tests/test_tools_execution.py` and verify all tests pass.
  - Route: Delegated / writer
  - Checks: `python -m unittest discover -s tests -v` passing 100%.
  - Evidence: Added `test_scan_tasks_empty`, `test_scan_tasks_with_odd_bitacora`, `test_scan_artifacts`, `test_status_api_idle_mode_and_version`, `test_serve_visual_blueprint_fallback`, and `test_serve_visual_mermaid_rendering`. 34/34 tests passed cleanly in 1.64s.

- [x] **TASK-04**: Commit changes, push to `origin/main`, and sync to local Antigravity skills.
  - Route: Delegated / writer
  - Checks: Git log clean, remote updated, local skill synchronized.
  - Evidence: Committed with conventional commit message `feat(cockpit): add authentic idle state, real artifacts explorer, and inferred mermaid diagrams`, pushed to `origin/main`, and copied updated tools to `C:\Users\iQuantum\.gemini\antigravity-cli\skills\q-agent\tools\q-cockpit\`.
