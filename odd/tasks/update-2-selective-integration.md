# Selective integration of update-2 fixes
Objective: adapt proposed audit and rollback fixes to current v2.12.0 without replacing workspace files. Baseline: `1e7fb77`.
Delivery: feature-branch-chain (local only), tracker `feature/update-2-integration`; runner: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. Forecast: approximately 900 authored changed lines; cohesive slices may exceed 400 where splitting would separate validation from its tests.

## Specs
- S1: "es que no seria reemplazar porque ya la version del workspace local tiene cambios seria validar linea por linea y de forma integral esos cambios propuestos". Compare proposed changes against current code and selectively adapt necessary fixes; preserve unrelated behavior and untracked `.scratch/` and `update-2/`.
- S2: "adelante". Implement the previously discussed fixes: truthful scope/status/evidence validation and per-item manifest parsing; fail-closed aggregation, opt-in root copies and current version label; expanded A02/A09 scope and default injection coverage; bounded correction passes and recoverable rollback preserving human changes. Verify through public CLIs with isolated temporary state and existing regression tests.
- S3: "encadenadas". Use local feature-branch-chain delivery; no push, PR creation or merge is authorized.

## Tasks
- T1 [S1,S2,S3] inline, implemented and functionally verified, native review pending; branch `fix/update-2-01-validation`; validator/parser contracts with tests and prompt/template docs; commit pending. Risk: item 3 (existing audit contract) and item 2 (evidence confinement).
- T2 [S1,S2,S3] inline, pending; branch `fix/update-2-02-reports`; aggregator/parser and runner compatibility with tests/help/docs; commit pending. Risk: item 3 (existing report/CLI contract).
- T3 [S1,S2,S3] inline, pending; branch `fix/update-2-03-coverage`; manifest scope/default level and bounded retries with tests/docs; commit pending. Risk: item 3 (consumed audit policy).
- T4 [S1,S2,S3] inline, pending; branch `fix/update-2-04-rollback`; preserve human changes with recoverable rollback policy and structural regression tests; commit pending. Risk: item 3 (consumed prompt) and item 1 (irreversible rollback effects).

## Log
- L1 Original request: "en /update-2 incluye unos fixes detectados, pero son de una version anterior, revisa que fixes fueron identificados en ese release y cuales aun estan presentes en la version actual."
- L2 User correction: "es que no seria reemplazar porque ya la version del workspace local tiene cambios seria validar linea por linea y de forma integral esos cambios propuestos".
- L3 Authorization: "adelante". Delivery selection: "encadenadas".
- L4 `git fetch origin` observed local and remote main both `1e7fb77`, v2.12.0. Package baseline is the same. Initial status: only untracked `.scratch/` and `update-2/`. Patch applicability check passes; not applied.
- L5 Read-only map identified proposed-patch gaps: self-citations, malformed tags, inline/fenced heading impostors, template inline comments, contradictory not_assessed severity, gaps and runner verdict parsing, missing rollback baseline. Adapt these within the requested fixes.
- L6 Route: parent writes inline; no parallel independent substantial writer units. Read-only explorer used because line-by-line mapping exceeded bounded parent evidence. Long full-suite runs and named high-risk verification delegate per action. RDD mode observed on (global); native assessment/review remains candidate-scoped.
- L7 Engram mirror pending: prior save failed because multiple active sessions match and no authoritative top-level session identity is exposed. Do not invent an identity or retry ambiguous saves.
- L8 T1 RED: 11 new public-CLI tests produced 14 assertion failures before implementation. GREEN: audit subset passed; full suite 188 tests passed. Independent verifier confirmed unchanged legacy output and nine legacy/technical/contracts flag combinations (technical timestamps differ naturally), filled template and all E01-E05 items accepted, and source hashes preserved on rejection. PyYAML parity could not run because PyYAML is unavailable; canonical fallback reads 22 items.
- L9 Independent verification found fenced example evidence could justify empty scope. One correction batch: committed regression observed RED, then excluded fenced lines from evidence body. All 12 targeted tests passed; independent blocker-only recheck confirmed rejection and invariant preservation. No open verifier blockers. Scratch retained until parent cleanup.
- L10 T1 slice keeps source validation, its regression tests and prompt/template contract together even if slightly above the advisory 400-line target; splitting those would leave an unverified contract. No PR size exception is asserted or authorized. Native review boundary remains baseline `1e7fb77`.
