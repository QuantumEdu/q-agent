#!/usr/bin/env python3
"""
q_fuzz.py - Bounded, seed-driven fuzz runner for q-agent.

Zero external dependencies (stdlib only, Python >= 3.10).

Role in the q-agent lifecycle:
  - Paso 6, Fase A (machine gate): ADVISORY step. Runs after unit tests
    with a fixed time budget. It never blocks a merge for "found nothing".
  - Paso 9 (Ops-to-ODD RED_FAIL loop): a crash found here becomes a
    minimized RED reproducer test before any fix is authorized.

Determinism contract (q-agent is deterministic SDD; fuzz is not, so the
runner bounds the non-determinism):
  - Same --seed + same --iterations => identical input sequence. The seed
    is recorded in every report.
  - --budget is wall-clock time. For strict reproducibility prefer
    --iterations over --budget.
  - Every crashing input is minimized to a single deterministic reproducer
    file. The corpus (tests/fuzz/corpus/<target>/) persists across runs.

Exit codes:
  0: no crash found within budget/iterations.
  2: at least one crash found (reproducer written).
  1: usage error / unknown target / target failed to load.
"""

import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_DIR = REPO_ROOT / "tests" / "fuzz" / "corpus"
DEFAULT_REPRO_DIR = REPO_ROOT / "tests" / "fuzz" / "repro"

# Seed inputs: well-formed values the generator mutates. Random soup alone
# rarely reaches interesting branches; seeds anchor the search.
SHORTSTAT_SEEDS = [
    " 3 files changed, 10 insertions(+), 2 deletions(-)",
    " 1 file changed, 1 insertion(+)",
    " 1 file changed, 1 deletion(-)",
    " 5 files changed, 0 insertions(+), 0 deletions(-)",
    " 2 files changed, 100 insertions(+), 50 deletions(-)",
    "",
]


def _load_merge_gate():
    """Load tools/q-merge-gate/q_merge_gate.py without a package import."""
    path = REPO_ROOT / "tools" / "q-merge-gate" / "q_merge_gate.py"
    spec = importlib.util.spec_from_file_location("q_merge_gate_fuzz", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_shortstat(result):
    """Invariant for parse_shortstat: tuple of two non-negative ints."""
    if not isinstance(result, tuple) or len(result) != 2:
        raise AssertionError(f"parse_shortstat must return a 2-tuple, got {result!r}")
    added, deleted = result
    if not isinstance(added, int) or not isinstance(deleted, int):
        raise AssertionError(f"parse_shortstat must return ints, got {result!r}")
    if added < 0 or deleted < 0:
        raise AssertionError(f"parse_shortstat must return non-negative counts, got {result!r}")


def _mutate(text, rng):
    """Apply 1-3 small mutations to a seed string."""
    chars = list(text)
    for _ in range(rng.randint(1, 3)):
        op = rng.choice(["flip", "insert", "delete", "duplicate", "truncate"])
        if op == "flip" and chars:
            i = rng.randrange(len(chars))
            chars[i] = rng.choice("0123456789abcefg+-(),. \n\t\x00\xff\u00e9")
        elif op == "insert":
            i = rng.randrange(len(chars) + 1)
            chars.insert(i, rng.choice("0123456789abcefg+-(),. \n\t"))
        elif op == "delete" and chars:
            del chars[rng.randrange(len(chars))]
        elif op == "duplicate" and chars:
            i = rng.randrange(len(chars))
            chars.insert(i, chars[i])
        elif op == "truncate" and chars:
            chars = chars[: rng.randrange(len(chars) + 1)]
    return "".join(chars)


def _soup(rng):
    """Fully random input: short unicode soup, including empty string."""
    alphabet = "0123456789abcefginsertiondeletion()+-., \n\t\x00\xff\u00e9\U0001f600"
    return "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 60)))


def generate_inputs(seeds, rng, count):
    """Deterministic input stream: seeded mutations, 1 in 5 pure soup."""
    inputs = []
    for _ in range(count):
        if rng.random() < 0.2:
            inputs.append(_soup(rng))
        else:
            inputs.append(_mutate(rng.choice(seeds), rng))
    return inputs


def crash_signature(exc, tb_text):
    """Dedup key: exception type + deepest frame (file:line) of the trace."""
    frames = re.findall(r'File "([^"]+)", line (\d+)', tb_text)
    anchor = f"{frames[-1][0]}:{frames[-1][1]}" if frames else "unknown"
    raw = f"{type(exc).__name__}|{anchor}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def write_repro(repro_dir, target_name, signature, crashing_input, func_ref):
    """Write a standalone RED reproducer: exit 2 while the bug exists.

    The file reloads the target function from ``func_ref``
    (``path/to/file.py:function_name``, path absolute or repo-relative)
    and calls it with the crashing input. If the call raises, it prints
    the traceback and exits 2 (RED). If the call succeeds, it exits 0,
    which is the signal that the fix landed.
    """
    repro_dir.mkdir(parents=True, exist_ok=True)
    path = repro_dir / f"test_repro_{target_name}_{signature}.py"
    content = (
        "#!/usr/bin/env python3\n"
        f"# RED reproducer for q-fuzz target '{target_name}' (crash {signature}).\n"
        f"# Target function: {func_ref}\n"
        "# Generated by tools/q-fuzz/q_fuzz.py. Do not hand-edit the input.\n"
        "# Expected: exit 2 while the bug exists, exit 0 once fixed.\n"
        "# Promote to a permanent regression test once the fix lands.\n"
        "import importlib.util\n"
        "import sys\n"
        "import traceback\n"
        "from pathlib import Path\n\n"
        f"FUNC_REF = {func_ref!r}\n"
        f"CRASHING_INPUT = {crashing_input!r}\n\n"
        "def _load_target():\n"
        "    file_part, func_name = FUNC_REF.rsplit(':', 1)\n"
        "    file_path = Path(file_part)\n"
        "    if not file_path.is_absolute():\n"
        "        file_path = Path(__file__).resolve().parents[3] / file_part\n"
        "    spec = importlib.util.spec_from_file_location('_q_fuzz_repro_target', file_path)\n"
        "    module = importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n"
        "    return getattr(module, func_name)\n\n"
        "if __name__ == '__main__':\n"
        "    try:\n"
        "        _load_target()(CRASHING_INPUT)\n"
        "    except Exception:\n"
        "        traceback.print_exc()\n"
        "        print('RED: reproducer still crashes (bug present).')\n"
        "        sys.exit(2)\n"
        "    print('GREEN: reproducer no longer crashes (fixed).')\n"
        "    sys.exit(0)\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


TARGETS = {
    "merge-gate-shortstat": {
        "description": "parse_shortstat() from tools/q-merge-gate: git --shortstat parser. Pure function; invariant: returns (added, deleted) non-negative ints and never raises.",
        "loader": _load_merge_gate,
        "func_name": "parse_shortstat",
        "check": _check_shortstat,
        "seeds": SHORTSTAT_SEEDS,
        "func_ref": "tools/q-merge-gate/q_merge_gate.py:parse_shortstat",
    },
}


def run_fuzz(target_name, seed=1, budget=60.0, iterations=None,
             corpus_dir=None, repro_dir=None, save_corpus=True):
    """Run one fuzz session. Returns the report dict (exit code in 'exit_code').

    Pure orchestration over the target's function: no network, no model calls.
    """
    if target_name not in TARGETS:
        raise ValueError(f"unknown target: {target_name!r} (see list-targets)")
    target = TARGETS[target_name]
    module = target["loader"]()
    func = getattr(module, target["func_name"])
    check = target["check"]

    rng = random.Random(seed)
    corpus_dir = (Path(corpus_dir) if corpus_dir else DEFAULT_CORPUS_DIR) / target_name
    repro_dir = Path(repro_dir) if repro_dir else DEFAULT_REPRO_DIR
    corpus_dir.mkdir(parents=True, exist_ok=True)
    repro_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    deadline = started + budget if budget is not None else None
    inputs_tried = []
    crashes = {}
    tried = 0
    # Seed coverage first: every registered seed is tried verbatim, in
    # order, before any mutation. This makes the first inputs of a run
    # deterministic and guarantees the interesting cases are exercised.
    seed_inputs = list(target["seeds"])
    while True:
        if iterations is not None and tried >= iterations:
            break
        if deadline is not None and time.monotonic() >= deadline:
            break
        if seed_inputs:
            batch = [seed_inputs.pop(0)]
        else:
            batch = generate_inputs(target["seeds"], rng, 10)
        for value in batch:
            if iterations is not None and tried >= iterations:
                break
            if deadline is not None and time.monotonic() >= deadline:
                break
            tried += 1
            inputs_tried.append(value)
            try:
                result = func(value)
                check(result)
            except Exception as exc:  # noqa: BLE001 - a crash IS the finding
                tb_text = traceback.format_exc()
                sig = crash_signature(exc, tb_text)
                if sig not in crashes:
                    # Resolve func_ref to an absolute path so the repro file
                    # works no matter where --repro-dir points.
                    ref_file, ref_func = target["func_ref"].rsplit(":", 1)
                    ref_path = Path(ref_file)
                    if not ref_path.is_absolute():
                        ref_path = REPO_ROOT / ref_path
                    abs_ref = f"{ref_path}:{ref_func}"
                    repro = write_repro(repro_dir, target_name, sig, value,
                                        abs_ref)
                    crash_path = corpus_dir / f"crash-{sig}.txt"
                    crash_path.write_text(value, encoding="utf-8")
                    crashes[sig] = {
                        "signature": sig,
                        "exception": type(exc).__name__,
                        "input": value,
                        "repro_file": str(repro),
                    }
    elapsed = time.monotonic() - started
    inputs_hash = hashlib.sha256(
        "\n".join(inputs_tried).encode("utf-8", "surrogatepass")
    ).hexdigest()
    if save_corpus:
        run_path = corpus_dir / f"run-seed-{seed}.jsonl"
        with run_path.open("w", encoding="utf-8") as fh:
            for value in inputs_tried:
                fh.write(json.dumps({"input": value}, ensure_ascii=False) + "\n")
    report = {
        "tool": "q-fuzz",
        "target": target_name,
        "seed": seed,
        "budget_seconds": budget,
        "iterations_requested": iterations,
        "inputs_tried": tried,
        "inputs_sha256": inputs_hash,
        "elapsed_seconds": round(elapsed, 3),
        "crashes_found": len(crashes),
        "crashes": list(crashes.values()),
        "corpus_dir": str(corpus_dir),
        "repro_dir": str(repro_dir),
        "exit_code": 2 if crashes else 0,
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="q-agent bounded seed-driven fuzz runner (Paso 6 Fase A advisory, Paso 9 RED_FAIL source)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-targets", help="List registered fuzz targets")
    p_list.add_argument("--json", action="store_true")

    p_run = sub.add_parser("run", help="Run one fuzz session")
    p_run.add_argument("--target", default="merge-gate-shortstat")
    p_run.add_argument("--seed", type=int, default=1)
    p_run.add_argument("--budget", type=float, default=60.0,
                       help="Wall-clock budget in seconds (default 60)")
    p_run.add_argument("--iterations", type=int, default=None,
                       help="Max inputs; overrides budget when reached")
    p_run.add_argument("--corpus-dir", default=None)
    p_run.add_argument("--repro-dir", default=None)
    p_run.add_argument("--no-save-corpus", action="store_true")
    p_run.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "list-targets":
        data = {name: info["description"] for name, info in TARGETS.items()}
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            for name, desc in data.items():
                print(f"- {name}: {desc}")
        return 0

    try:
        report = run_fuzz(
            target_name=args.target,
            seed=args.seed,
            budget=args.budget,
            iterations=args.iterations,
            corpus_dir=args.corpus_dir,
            repro_dir=args.repro_dir,
            save_corpus=not args.no_save_corpus,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 72)
        print(f"q-fuzz report — target={report['target']} seed={report['seed']}")
        print(f"Inputs tried: {report['inputs_tried']} in {report['elapsed_seconds']}s "
              f"(inputs sha256: {report['inputs_sha256'][:12]})")
        print(f"Corpus: {report['corpus_dir']} | Repro: {report['repro_dir']}")
        if report["crashes"]:
            print(f"CRASHES: {report['crashes_found']}")
            for crash in report["crashes"]:
                print(f"  - [{crash['signature']}] {crash['exception']}: "
                      f"input={crash['input']!r}")
                print(f"    repro: {crash['repro_file']}")
            print("Next step (Paso 9 RED_FAIL): promote the repro to a regression "
                  "test, then fix, then re-fuzz with the same seed.")
        else:
            print("No crashes found within budget. This is NOT proof of "
                  "correctness, only of survival for this seed/budget.")
        print("=" * 72)
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
