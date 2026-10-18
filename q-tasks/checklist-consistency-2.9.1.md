# Checklist consistency patch

- Date: 2026-10-18
- Release: 2.9.1 (patch)
- Execution: standalone, one cohesive generator/configuration slice
- Status: verified; independent review APPROVED

## Acceptance

- UAC-01: Constitution and ADR reflect each selected architecture; modular
  monoliths use functional slices without mandatory global hexagonal layers.
- UAC-02: Template and generated configuration leave executor and model IDs null
  until verified/configured for the actual host.
- UAC-03: Shared defaults remain aligned and selected workspace isolation is kept.
- UAC-04: Package, skill, README, integrity checks and changelog use patch 2.9.1.

## Work

- [x] TASK-01: Correct generator and template, document setup and add CLI regressions.

## Terminal evidence

| Check | Exit | Observed result |
|---|---|---|
| New CLI regression suite before fix | 1 | 4 tests, 7 failing assertions/subtests reproducing drift |
| New CLI regression suite after fix | 0 | 4 tests passed; real subprocesses and files, no mocks |
| Full unittest discovery, Python 3.10.21 | 0 | 102 tests passed |
| Full unittest discovery, Python 3.11.16 | 0 | 102 tests passed |
| Full unittest discovery, Python 3.12.14 | 0 | 102 tests passed |
| `bash bin/q-agent --version` | 0 | v2.9.1 |
| Compilation, JSON, shell syntax, CLI help/capabilities and benchmark smoke | 0 | All checks passed |
| Independent adversarial review | — | APPROVED; no open R IDs; reviewer independently reran 102 tests on Python 3.12.14 |

Full-suite command: `Q_COCKPIT_HOME=<temporary-directory> python3 -m unittest discover -s tests -v`.
See `REVIEW.md` for final review and publication evidence.

Existing project artifacts require deliberate manual reconciliation; this patch
does not regenerate or migrate them. No database, HTTP or UI runtime changed.
