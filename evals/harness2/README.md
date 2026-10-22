# q-agent Harness² Evaluation Suite

This directory contains the contrastive evaluation suites for `q-agent` applying the principles of **Harness²** ([arXiv:2610.14224](https://arxiv.org/abs/2610.14224), Google Research).

The runners preserve strict experimental discipline:
- **Immutable Tests:** SHA-256 fingerprinted test files before each phase (`tampered=True` on mismatch).
- **Zero Mocks:** Real SQLite WAL instances with foreign key constraints.
- **Cold-Start Recovery:** Multi-session runs use `codex exec --ephemeral` without retained conversation history.
- **Independent Adversarial Review:** Code changes pass through an isolated review gate before approval.

---

## 1. Local Evaluator Scripts

Run any of the evaluation suites directly with Python:

```bash
# 1. Base Prototype (SQLite ticket workflow, WAL, and state machine)
python3 evaluator.py

# 2. Stress & Migration (Multi-tenant RBAC & schema rollback)
python3 stress_evaluator.py

# 3. Concurrency & Contention (10-worker race & 20-thread WAL bursts)
python3 concurrency_evaluator.py

# 4. Context Recovery (3 ephemeral cold-start sessions with SLA regression)
python3 recovery_evaluator.py

# 5. Chaos Engineering & Crash Recovery (SIGKILL, post-crash lock bursts & torn WAL frame recovery)
python3 chaos_evaluator.py
```

Results, diffs, and trajectory logs are saved under `runs/`, `stress_runs/`, `concurrency_runs/`, `recovery_runs/`, and `chaos_runs/`.

---

## 2. Official JobBench Benchmark

For official JobBench benchmark execution under the Harness² recursive adaptation framework (Propose–Probe–Compose with DeepSeek), see the complete report and reproduction steps in:
[`docs/validation/harness2-evaluation.md`](../../docs/validation/harness2-evaluation.md) and [`QuantumEdu/harness2`](https://github.com/QuantumEdu/harness2).
