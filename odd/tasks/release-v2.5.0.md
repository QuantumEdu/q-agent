# Release: q-agent v2.5.0

- **Feature Name**: `release-v2.5.0`
- **Objective**: Cut the official SemVer MINOR release `v2.5.0` incorporating Cockpit v2, Deterministic Technical Contracts Audit Gate, Context-Isolated Adversarial Review Gate, and Wave Execution & Vertical Slices architecture alignment.
- **Why**: Solidify all accumulated backward-compatible features since v2.4.0 under a formal release boundary with consistent version metadata and Git tag.
- **Scope**:
  - `skill.json`, `SKILL.md`, `README.md`
  - `CHANGELOG.md` (formalize 2.5.0 release notes, start fresh Unreleased)
  - `tests/test_skill_integrity.py` (update assertions to 2.5.0)
  - `tools/q-audit-aggregator/generate_report.py`, `tools/q-audit-validator/validate_audit.py`, `tools/q-cockpit/ui/index.html`
  - Git tag `v2.5.0` and synchronization to local skill.
- **Constraints**:
  - Zero test regressions (28/28 tests passing).
  - Clean SemVer 2.0.0 compliance.
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Bump version metadata to `2.5.0` across `skill.json`, `SKILL.md`, `README.md`, tools, and update `CHANGELOG.md`.
  - Route: Delegated / writer
  - Checks: Exact string matching of `2.5.0` across all metadata files (VERIFIED).

- [x] **TASK-02**: Update test assertions in `tests/test_skill_integrity.py` and verify all tests pass.
  - Route: Delegated / writer
  - Checks: `python -m unittest discover -s tests -v` passing 100% (28/28 tests passed).

- [x] **TASK-03**: Commit release, create annotated Git tag `v2.5.0`, push to remote, and sync local Antigravity skill directory.
  - Route: Delegated / writer
  - Checks: `git tag -l` contains `v2.5.0`, remote pushed, local skill synchronized.
