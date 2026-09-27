# Feature: Cockpit Interactive Mermaid Pan & Zoom Viewer

- **Feature Name**: `cockpit-mermaid-pan-zoom`
- **Objective**: Implement an interactive Pan & Zoom viewport with Fullscreen support in `q-cockpit` for Mermaid diagrams (`/visual`), eliminating the destructive proportional shrinking of wide architecture diagrams.
- **Why**: Wide diagrams (like `README.md` flowchart) shrink to 20% width and become completely illegible ribbons without zoom or scroll controls.
- **Scope**:
  - `tools/q-cockpit/q_cockpit.py`:
    - Refactor `_render_mermaid_page()` to include:
      - Per-diagram zoom controls: Zoom In (`+`), Zoom Out (`-`), Real Size (`1:1`), Fit to Screen (`↔ Fit`), and Fullscreen (`⛶`).
      - Scalable viewport (`transform: scale(...)`) with smooth transitions.
      - Click & Drag Pan navigation (`cursor: grab / grabbing`).
      - Wheel zoom (`Ctrl + Wheel`).
      - Native custom dark scrollbars (`overflow: auto`).
      - Removal of Mermaid's aggressive `max-width: 100%` on SVGs so typography stays crisp at native font sizes.
  - `tests/test_tools_execution.py`:
    - Update test asserting zoom controls and pan/zoom markup in `serve_visual`.
- **Constraints**:
  - Pure vanilla JavaScript, zero external libraries.
  - 100% test suite passing.
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Implement interactive Pan & Zoom, controls toolbar, drag-to-pan, and fullscreen in `_render_mermaid_page` within `tools/q-cockpit/q_cockpit.py`.
  - Route: Delegated / writer
  - Checks: HTML contains zoom buttons, pan event handlers, and scalable diagram viewports.
  - Evidence: `_render_mermaid_page` includes `.zoom-toolbar`, `.zoom-btn`, `.diagram-viewport`, SVG `max-width: none !important`, drag-and-pan mouse events, wheel zoom with cursor centering, and full-window modal overlay.

- [x] **TASK-02**: Update unit tests in `tests/test_tools_execution.py` and verify all tests pass.
  - Route: Delegated / writer
  - Checks: `python -m unittest discover -s tests -v` passing 100%.
  - Evidence: Verified 34/34 tests pass, including `test_serve_visual_mermaid_rendering` asserting presence of `zoom-btn`, `zoomDiagram`, `fitDiagram`, `toggleFullscreen`, and `diagram-viewport`.

- [x] **TASK-03**: Commit changes, push to `origin/main`, and sync to local Antigravity skills.
  - Route: Delegated / writer
  - Checks: Git log clean, remote updated, local skill synchronized.
  - Evidence: Synced to `C:\Users\iQuantum\.gemini\antigravity-cli\skills\q-agent\tools\q-cockpit\q_cockpit.py`, commit created and pushed to `origin/main`.
