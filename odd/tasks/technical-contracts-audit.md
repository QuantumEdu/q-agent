# Feature: Technical Contracts Audit (Disaster Recovery, CI & Observability)

- **Feature Name**: `technical-contracts-audit`
- **Objective**: Implement deterministic static audit gates for Disaster Recovery (A17), GitHub CI Integrity (A03), and Observability/Telemetry (A14) via a standalone script (`scripts/audit_api_contracts.js`) and within `tools/q-audit-validator/validate_audit.py`.
- **Why**: Prevent AI hallucination and token waste by providing fast, zero-dependency deterministic checks for critical infrastructure contracts before deeper semantic LLM auditing.
- **Scope**:
  - `scripts/audit_api_contracts.js`: Node.js deterministic validator for CI, Disaster Recovery, Observability, and API contracts.
  - `tools/q-audit-validator/validate_audit.py`: Add `--mode technical` to execute the deterministic contracts audit natively in Python without external dependencies.
  - `tests/test_audit_validator.py`: Unit tests asserting technical contract validation behavior.
- **Constraints**:
  - Zero external npm/pip dependencies.
  - Native Python 3 standard library and Node.js standard library (`fs`, `path`).
  - Output structured JSON and clean CLI terminal reports with exit code 0 (pass) / 1 (fail).
- **Mirror Status**: Pending (Engram MCP service unavailable in session).

---

## Tasks

- [x] **TASK-01**: Implement `scripts/audit_api_contracts.js` with Disaster Recovery, GitHub CI, Observability, and API routes validation.
  - Route: Delegated / writer
  - Checks: `node scripts/audit_api_contracts.js --cwd .` passes cleanly on compliant repos or reports concrete gaps.
  - Evidence: Verified with `--cwd .`, `--json`, and `--strict`. Zero external npm dependencies.

- [x] **TASK-02**: Add `--mode technical` to `tools/q-audit-validator/validate_audit.py` with matching deterministic checks in pure Python.
  - Route: Delegated / writer
  - Checks: `python tools/q-audit-validator/validate_audit.py --mode technical` executes and outputs report.
  - Evidence: Verified `--mode technical`, `--mode contracts`, `--json`, `--strict`. Zero external dependencies.

- [x] **TASK-03**: Add unit test coverage in `tests/test_audit_validator.py` and verify all 23+ tests pass.
  - Route: Inline / test verification
  - Checks: `python -m unittest discover -s tests -v` passing 100% (28/28 tests passed).
  - Evidence: Unit tests for technical contracts validation, full compliance, missing criticals, CLI invocation, and Node.js script.

