# q-agent 2.9.1 — Checklist consistency fix

Choosing a modular monolith previously generated hexagonal principles, ports and
adapters in its constitution and ADR. The configuration also claimed a specific
executor and model IDs without checking the actual environment.

The generator now uses architecture-specific principles, components and tradeoffs.
It loads the complete shared JSON template, overrides the selected isolation and
leaves executor/models unconfigured (`null`). The CLI and documentation explain
that these fields need verified environment-specific values. Interactive option
numbers and defaults are preserved. The package release advances from 2.9.0 to
2.9.1; the configuration format remains 1.2.

## Verification

| Evidence | Result |
|---|---|
| New regressions before fix | Exit 1: four tests, seven failing assertions/subtests |
| Full suites on Python 3.10.21 / 3.11.16 / 3.12.14 | Exit 0: 102 tests per interpreter |
| Compilation, JSON, shell syntax, CLI smoke and benchmark | Exit 0 |
| CLI package version | v2.9.1 |
| Independent read-only adversarial review | APPROVED; no blocking findings or open R IDs |

The reviewer independently reran all 102 tests on Python 3.12.14. The CLI
regressions exercise real subprocesses and filesystem artifacts across all four
architectures and both isolation choices. See the
[task evidence](q-tasks/checklist-consistency-2.9.1.md).

## Scope and publication

Existing project artifacts are not migrated. Reconcile them manually to preserve
custom decisions; rerunning the checklist overwrites its three output files.
No live model inference, remote runtime or production application deployment is
part of this patch. Remote GitHub CI and release publication are not certified
by local test results.

The user previously authorized direct pushes to main. Publish this patch with
a normal fast-forward push after the deterministic merge gate passes.
