# Flight Recorder Protocol (Observability & Audit Trail)

The Flight Recorder is a zero-dependency, append-only execution log maintained by `q-agent` inside `<PROJECT_ROOT>/.q-agent/flight_recorder.log`.

It serves as a deterministic "black box" audit trail to detect bottlenecks, broken paths, missing files, failed credentials, and tool failures in real time without cognitive overload.

---

## 1. Storage Location & Lifecycle
- **Path:** `<PROJECT_ROOT>/.q-agent/flight_recorder.log`
- **Format:** Plaintext append-only log, one line per milestone event.
- **Git policy:** Committed by default so architectural progress and execution history remain verifiable, or added to `.gitignore` if the team prefers ephemeral logs.

---

## 2. Event Format Specification

Every log line follows a strict bracketed timestamp and tag structure:

```text
[YYYY-MM-DDTHH:MM:SSZ] [STEP_ID] [EVENT_TYPE] [STATUS] Details / Evidence
```

### Event Types
| Event Type | Purpose | Example Status |
|---|---|---|
| `[PREFLIGHT]` | Verification of runtime prerequisites (`gh auth status`, `git status`) | `OK`, `FAIL` |
| `[BOUNDARY]` | Path boundary verification (`<SKILL_ROOT>` vs `<PROJECT_ROOT>`) | `RESOLVED`, `WARN` |
| `[CONFIG]` | Declarative configuration discovery (`.q-agent.json`) | `LOADED`, `DEFAULT` |
| `[ROUTING]` | Decision on runtime executor, Tier 1 model, Tier 2 model | `ASSIGNED` |
| `[SKILL_CALL]` | Invocation of auxiliary sub-skills (`q-deliberate`, `q-ci-fixer`, etc.) | `INVOKED`, `COMPLETED`, `FAIL` |
| `[GATE]` | Human-in-the-loop checkpoints (Step 0, Step 3, Scope gate, Tradeoffs) | `PENDING`, `APPROVED`, `REJECTED` |
| `[INTERACTION]` | Interactive prompt/question to user at phase gates | `PROMPT`, `ANSWERED`, `SKIPPED` |
| `[LINTER]` | Local linter/testing verification runs | `PASS (0 tokens)`, `FAIL` |
| `[ERROR]` | File not found, permission error, command failure | `BLOCKED`, `RECOVERED` |
| `[MERGE]` | Branch integration completed | `OK`, `CONFLICT` |
| `[WORKTREE]` | Isolated git worktree lifecycle | `CREATED`, `REMOVED` |
| `[REPRODUCTION]` | Red-phase reproduction test verification (SWE-agent pattern) | `RED_FAIL`, `GREEN_PASS` |
| `[AST_INDEX]` | AST skeleton extraction / context pruning | `EXTRACTED`, `CACHED` |
| `[ROLLBACK]` | Atomic reset/revert on unrecoverable failure | `EXECUTED`, `ABORTED` |
| `[GITHUB_SYNC]` | Issues or PRs registered via GitHub CLI | `CREATED`, `SKIPPED` |

---

## 2.1. Matriz de Evaluación de Agentes (9 Dimensiones LLMOps)

Configurable en `.q-agent.json` vía `observability.eval_level`:

| Dimensión | Descripción | Mapeo en Flight Recorder | Niveles |
|---|---|---|---|
| **`decision`** | Acierto y justificación de decisiones de arquitectura y negocio | `[GATE]`, `[ADR]` | `standard`, `enterprise` |
| **`evidence`** | Sustento fáctico sin alucinaciones comprobado en código | `[OBSERVADO]`, `[AST_INDEX]` | `standard`, `enterprise` |
| **`tools`** | Selección e invocación eficiente y limpia de herramientas | `[SKILL_CALL]`, `[LINTER]` | `standard`, `enterprise` |
| **`routing`** | Enrutamiento óptimo entre modelos Tier 1 y Tier 2 | `[CONFIG]`, `[ROUTING]` | `standard`, `enterprise` |
| **`retries`** | Control de bucles de falla y recuperación determinista | `[ERROR]`, `[RECOVERED]`, `[ROLLBACK]` | `standard`, `enterprise` |
| **`cost`** | Consumo de tokens e inversión en USD por fase | `[TELEMETRY] [TOKENS]` | `enterprise` |
| **`latency`** | Duración de ejecución (wall-clock seconds) por paso | `[TELEMETRY] [LATENCY]` | `enterprise` |
| **`policy compliance`** | Apego a la Constitución, límites y seguridad | `[CAB_RP]`, `[BOUNDARY]` | `minimal`, `standard`, `enterprise` |
| **`final outcome`** | Veredicto funcional: código compila y tests pasan al 100% | `[LINTER] [PASS]`, `[CLOSURE]` | `minimal`, `standard`, `enterprise` |

### Niveles de Madurez de Evaluación:
- **`minimal`**: Mide únicamente `final outcome` y `policy compliance`. Ideal para micro-parches rápidos (Fast Path) y prototipos de 1 persona.
- **`standard` (Por Defecto)**: Agrega `decision`, `evidence`, `tools`, `routing` y `retries`. Mantiene alta calidad de ingeniería sin sobrecarga de medición.
- **`enterprise`**: Activa las 9 dimensiones completas sumando `cost` y `latency` para contabilidad estricta y SLAs corporativos.

## 3. Reference Log Stream Example

```log
[2026-09-13T18:00:01Z] [STEP-00] [CONFIG] [LOADED] .q-agent.json found: runtime=antigravity tier1=gemini-3.8-flash
[2026-09-13T18:00:02Z] [STEP-00] [BOUNDARY] [RESOLVED] SKILL_ROOT=~/.pi/agent/skills/q-agent PROJECT_ROOT=D:/02-A/code/demo
[2026-09-13T18:00:03Z] [STEP-01] [PREFLIGHT] [OK] gh auth status confirmed (QuantumEdu)
[2026-09-13T18:00:15Z] [STEP-02] [SKILL_CALL] [INVOKED] q-deliberate (Proponent -> Adversary -> Synthesizer)
[2026-09-13T18:00:30Z] [STEP-02] [SKILL_CALL] [COMPLETED] docs/adr/0001-runtime-stack.md generated
[2026-09-13T18:00:45Z] [STEP-03] [GATE] [APPROVED] Runtime gate confirmed: single-agent antigravity tier1=gemini-3.8-flash
[2026-09-13T18:01:00Z] [STEP-04] [PREFLIGHT] [OK] Private GitHub repository initialized and CONSTITUTION.md committed
[2026-09-13T18:02:10Z] [STEP-05] [GATE] [APPROVED] P04 /propose scope confirmed by user
[2026-09-13T18:03:00Z] [STEP-06] [LINTER] [PASS] local pytest exit code 0 (0 LLM tokens spent)
[2026-09-13T18:04:15Z] [STEP-07] [SKILL_CALL] [COMPLETED] P09 CAB-RP Compliance Audit: 0 drift, 100% contracts validated
```

---

## 4. Error Diagnostics & Triage Protocol

If `q-agent` halts or encounters an unexpected state:
1. **Never guess or retry blindly.** Inspect the tail of `.q-agent/flight_recorder.log`:
   ```bash
   tail -n 20 .q-agent/flight_recorder.log
   ```
2. **Path check:** Confirm that `<SKILL_ROOT>` and `<PROJECT_ROOT>` did not cross boundaries.
3. **Sub-skill check:** Check whether a sub-skill (`q-ci-fixer`, `q-deliberate`) exited with non-zero or missing output.
4. **Recovery:** Record `[ERROR] [RECOVERED]` upon applying a corrective patch.
