# Feature: SkillVault Explorer & Zero-Dependency Terminal TUI

- **Feature Name**: `skillvault-explorer-and-tui`
- **Objective**:
  1. Add SkillVault search, preview, and copy-paste capabilities to `q-cockpit`, governed by `context_retrieval.providers.skillvault.enabled` in `.q-agent.json`.
  2. Implement a zero-dependency native Python Terminal User Interface (TUI) for headless / SSH / terminal-only environments.
- **Why**:
  - Engineers need to search and reuse skills without polluting AI context or relying on automatic token ingestion.
  - Headless/SSH environments need a fast, dependency-free dashboard to monitor project status and tasks without browser port forwarding.
- **Scope**:
  - `templates/q-agent.json`: Add skillvault path configuration support.
  - `tools/q-cockpit/q_cockpit.py`:
    - Add `/api/skillvault` endpoint respecting `context_retrieval.providers.skillvault.enabled`.
    - Add `--tui` CLI flag delegating to the TUI runner.
  - `tools/q-cockpit/ui/index.html`:
    - Add SkillVault explorer tab with search, markdown preview, and copy-to-clipboard functionality.
    - Localize with ES/EN i18n keys.
  - `tools/q-cockpit/q_cockpit_tui.py`:
    - Pure Python zero-dependency ANSI TUI dashboard (Overview, Tasks, Commits, SkillVault).
  - `justfile`: Add `cockpit-tui` recipe.
  - `tests/test_tools_execution.py`: Unit tests for SkillVault API and TUI modules.
- **Constraints**:
  - Zero external pip/npm dependencies (runs in standard Python 3.10+ on Windows, Linux, WSL, macOS).
  - 100% test suite passing (all 45 tests).
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Implement SkillVault discovery and API endpoint in `tools/q-cockpit/q_cockpit.py` governed by configuration.
  - Route: Delegated / writer
  - Checks: `/api/skillvault` returns enabled status and discovered skills.

- [x] **TASK-02**: Add SkillVault tab to Cockpit UI (`ui/index.html`) with live search, preview, and clipboard copy.
  - Route: Delegated / writer
  - Checks: UI renders enabled state with copy buttons or clear disabled state.

- [x] **TASK-03**: Create zero-dependency cross-platform Python TUI (`tools/q-cockpit/q_cockpit_tui.py`) and wire `--tui` in `q_cockpit.py` and `justfile`.
  - Route: Delegated / writer
  - Checks: TUI launches, renders dashboard, handles tab navigation, and exits cleanly.

- [x] **TASK-04**: Add unit tests in `tests/test_tools_execution.py`, commit changes, push to `origin/main`, and sync local Antigravity skills.
  - Route: Delegated / writer
  - Checks: All unit tests pass, remote pushed, local skill synchronized.

---

## Terminal Evidence (P06 Verification)

| Wave | Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Estado |
|---|---|---|---|---|---|
| Wave 1 | TASK-01 | `python tools/q-cockpit/q_cockpit.py --help` | `0` | Subparsers `{serve,tui,new,wait}` and flag `--tui` verified | Verified |
| Wave 1 | TASK-02 | `python -c "assert 'tab_skillvault' in open('tools/q-cockpit/ui/index.html').read()"` | `0` | Tab 5 button, container, ES/EN I18N keys and JS handlers verified | Verified |
| Wave 1 | TASK-03 | `python tools/q-cockpit/q_cockpit_tui.py --view 1 --once` | `0` | ANSI TUI rendered Dashboard, Kanban, Diff, and SkillVault views | Verified |
| Wave 1 | TASK-04 | `python -m unittest discover -s tests -v` | `0` | Ran 45 tests in 2.178s. All 45 tests passing cleanly. | Verified |
