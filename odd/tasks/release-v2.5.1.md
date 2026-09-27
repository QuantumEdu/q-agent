# Release: q-agent v2.5.1

- **Feature Name**: `release-v2.5.1`
- **Objective**: Cut formal SemVer PATCH release `v2.5.1` packaging the q-cockpit authenticity upgrades: authentic idle state with recent Git commits, elimination of fake pipeline mocks, real project artifacts explorer, and inferred live Mermaid diagrams.
- **Why**: Package stable Cockpit improvements under a dedicated, tagged release boundary following SemVer 2.0.0 and Option A release governance.
- **Scope**:
  - `skill.json`: bump to `2.5.1`
  - `SKILL.md`: bump to `2.5.1` in YAML frontmatter and titles
  - `README.md`: bump badges and references to `v2.5.1`
  - `CHANGELOG.md`: document `## [2.5.1] - 2026-09-26`
  - `tests/test_skill_integrity.py`: update version assertion to `2.5.1`
  - `tools/q-audit-aggregator/generate_report.py`, `tools/q-audit-validator/validate_audit.py`, `tools/q-cockpit/ui/index.html`: update version strings
  - Git tag `v2.5.1` and synchronization to local skill.
- **Constraints**:
  - 100% test suite passing (34/34 tests).
  - Clean SemVer 2.0.0 compliance.
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Bump version metadata to `2.5.1` across `skill.json`, `SKILL.md`, `README.md`, tools, and update `CHANGELOG.md`.
  - Route: Delegated / writer
  - Checks: Exact string matching of `2.5.1` across all metadata files (VERIFIED).

- [x] **TASK-02**: Update test assertions in `tests/test_skill_integrity.py` and verify all tests pass.
  - Route: Delegated / writer
  - Checks: `python -m unittest discover -s tests -v` passing 100% (34/34 tests passing).

- [x] **TASK-03**: Commit release, create annotated Git tag `v2.5.1`, push to remote, and sync local Antigravity skill directory.
  - Route: Delegated / writer
  - Checks: `git tag -l` contains `v2.5.1`, remote pushed, local skill synchronized.
