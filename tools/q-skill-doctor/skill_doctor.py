"""q-skill-doctor: score past agent conversations and propose skill improvements.

The loop, adapted from the Warp Skill Doctor design to q-agent's constraints:

  1. AGGREGATE  read real transcripts from local agent runtimes into one corpus.
  2. SCORE      compute deterministic signals per session and per skill against
                a fixed rubric (efficiency, quality, coverage).
  3. IMPROVE    emit merge-ready proposals, each bound to evidence (session ids
                and counts) and handed to q-improve-loop for the rewrite.

What this tool deliberately does NOT do:
  - It never edits a SKILL.md. Proposals are drafts; a human or q-improve-loop
    applies them. A scoring tool with write access to what it scores is a
    self-fulfilling feedback loop with no external check.
  - It never sends content anywhere. Everything stays in a local SQLite file.

Only the standard library is used, matching the rest of q-agent.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

MAX_LINES_PER_FILE = 20000
MAX_TEXT_CHARS = 2000

TEST_COMMAND = re.compile(
    r"\b(pytest|py_compile|unittest|just test|npm (run )?test|pnpm test|go test|cargo test|"
    r"vitest|jest|make test|ruff|mypy|tsc)\b",
    re.IGNORECASE,
)
WRITE_TOOL = re.compile(
    r"(write|edit|patch|apply_patch|create_file|str_replace|multiedit|update_file)", re.IGNORECASE
)

KINDS = ("user_message", "assistant_message", "tool_call", "tool_result", "error")


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel_home() -> Path:
    return Path.home()


# --------------------------------------------------------------- corpus


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            path TEXT NOT NULL,
            started_at TEXT,
            cwd TEXT,
            model TEXT,
            ingested_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions (session_id),
            seq INTEGER NOT NULL,
            ts TEXT,
            kind TEXT NOT NULL,
            role TEXT,
            name TEXT,
            text TEXT,
            status TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id, seq);
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """
    )
    db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
    db.commit()
    return db


def store(db: sqlite3.Connection, session: dict, events: list[dict]) -> None:
    with db:
        db.execute(
            "INSERT OR REPLACE INTO sessions (session_id, source, path, started_at, cwd, model, ingested_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session["session_id"], session["source"], session["path"], session.get("started_at"),
             session.get("cwd"), session.get("model"), utcnow()),
        )
        db.execute("DELETE FROM events WHERE session_id = ?", (session["session_id"],))
        db.executemany(
            "INSERT INTO events (session_id, seq, ts, kind, role, name, text, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (session["session_id"], index, event.get("ts"), event["kind"], event.get("role"),
                 event.get("name"), (event.get("text") or "")[:MAX_TEXT_CHARS], event.get("status"))
                for index, event in enumerate(events)
            ],
        )


def read_lines(path: Path):
    try:
        with path.open("r", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index >= MAX_LINES_PER_FILE:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


# --------------------------------------------------------------- adapters


def adapt_codex(path: Path) -> tuple[dict, list[dict]]:
    """Codex CLI rollout transcripts (JSONL)."""
    events: list[dict] = []
    meta = {"session_id": path.stem, "source": "codex", "path": str(path)}
    for record in read_lines(path):
        payload = record.get("payload") or {}
        if record.get("type") == "session_meta":
            meta["session_id"] = payload.get("session_id") or meta["session_id"]
            meta["cwd"] = payload.get("cwd")
            meta["started_at"] = record.get("timestamp")
            meta["model"] = payload.get("model")
            continue
        ptype = payload.get("type")
        ts = record.get("timestamp")
        if ptype == "message":
            role = payload.get("role")
            text = " ".join(
                item.get("text", "")
                for item in payload.get("content") or []
                if isinstance(item, dict)
            )
            kind = {"user": "user_message", "assistant": "assistant_message"}.get(role, "tool_result")
            if text:
                events.append({"ts": ts, "kind": kind, "role": role, "text": text})
        elif ptype == "custom_tool_call":
            events.append({"ts": ts, "kind": "tool_call", "role": "assistant",
                           "name": payload.get("name"), "text": str(payload.get("input") or ""),
                           "status": payload.get("status")})
        elif ptype == "custom_tool_call_output":
            events.append({"ts": ts, "kind": "tool_result", "name": payload.get("name"),
                           "text": str(payload.get("output") or ""), "status": payload.get("status")})
        elif ptype == "reasoning":
            events.append({"ts": ts, "kind": "assistant_message", "role": "assistant",
                           "text": str(payload.get("content") or "")})
        elif ptype == "task_complete":
            events.append({"ts": ts, "kind": "tool_result", "name": "task_complete", "text": ""})
    return meta, events


def adapt_antigravity(path: Path) -> tuple[dict, list[dict]]:
    """Antigravity CLI step transcripts (JSONL)."""
    events: list[dict] = []
    base = path.parents[2].name if len(path.parents) > 2 else path.stem
    meta = {"session_id": f"agy:{base}", "source": "agy", "path": str(path)}
    for record in read_lines(path):
        ts = record.get("created_at")
        rtype = record.get("type")
        content = record.get("content")
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False) if content else ""
        if rtype == "USER_INPUT":
            events.append({"ts": ts, "kind": "user_message", "role": "user", "text": text})
        elif rtype == "PLANNER_RESPONSE":
            events.append({"ts": ts, "kind": "assistant_message", "role": "assistant", "text": text})
        elif rtype == "SYSTEM_MESSAGE":
            events.append({"ts": ts, "kind": "tool_result", "role": "system", "text": text})
        for call in record.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            events.append({
                "ts": ts, "kind": "tool_call", "role": "assistant",
                "name": call.get("name"),
                "text": json.dumps(call.get("args"), ensure_ascii=False)[:MAX_TEXT_CHARS],
                "status": record.get("status"),
            })
        if record.get("status") == "ERROR":
            events.append({"ts": ts, "kind": "error", "text": text or "step reported ERROR"})
    return meta, events


def adapt_opencode(db_path: Path, limit: int = 200) -> list[tuple[dict, list[dict]]]:
    """OpenCode session database (SQLite)."""
    if not db_path.exists():
        return []
    source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    sessions: list[tuple[dict, list[dict]]] = []
    try:
        rows = source.execute(
            "SELECT id, title, directory, model, tokens_input, tokens_output "
            "FROM session_v2 ORDER BY time_updated DESC LIMIT ?",
            (limit,),
        ).fetchall()
        for row in rows:
            meta = {"session_id": row["id"], "source": "opencode", "path": str(db_path),
                    "cwd": row["directory"], "model": row["model"]}
            events: list[dict] = []
            for message in source.execute(
                "SELECT type, seq, time_created, data FROM session_message "
                "WHERE session_id = ? ORDER BY seq",
                (row["id"],),
            ):
                try:
                    data = json.loads(message["data"])
                except (TypeError, json.JSONDecodeError):
                    data = {}
                text = data.get("text") or data.get("content") or ""
                mtype = message["type"]
                kind = {"user": "user_message", "assistant": "assistant_message"}.get(mtype, "tool_result")
                events.append({
                    "ts": str(message["time_created"]),
                    "kind": kind,
                    "role": mtype,
                    "name": data.get("tool") or data.get("name"),
                    "text": text if isinstance(text, str) else json.dumps(text, ensure_ascii=False),
                })
            sessions.append((meta, events))
    except sqlite3.Error:
        return sessions
    finally:
        source.close()
    return sessions


def adapt_jsonl(path: Path) -> tuple[dict, list[dict]]:
    """Generic adapter: {role, content} or {kind, text} records.

    Lets any runtime join the corpus without a new adapter, which is the whole
    point of keeping the canonical event shape small.
    """
    events: list[dict] = []
    for record in read_lines(path):
        kind = record.get("kind")
        if not kind:
            role = record.get("role")
            kind = {"user": "user_message", "assistant": "assistant_message"}.get(role, "tool_result")
        events.append({
            "ts": record.get("ts") or record.get("timestamp"),
            "kind": kind,
            "role": record.get("role"),
            "name": record.get("name"),
            "text": str(record.get("text") or record.get("content") or ""),
        })
    return {"session_id": path.stem, "source": "jsonl", "path": str(path)}, events


# --------------------------------------------------------------- scoring


def skill_names(skills_root: Path) -> list[str]:
    names = []
    for skill in sorted((skills_root / "skills").glob("*/SKILL.md")):
        names.append(skill.parent.name)
    return names


def load_events(db: sqlite3.Connection, session_id: str) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM events WHERE session_id = ? ORDER BY seq", (session_id,)
    ).fetchall()


def score_session(events: list[sqlite3.Row], available: list[str]) -> dict:
    user_turns = sum(1 for e in events if e["kind"] == "user_message")
    tool_calls = [e for e in events if e["kind"] == "tool_call"]
    errors = [e for e in events if e["kind"] == "error" or e["status"] == "ERROR"]

    signatures = Counter()
    for call in tool_calls:
        signatures[((call["name"] or "?"), (call["text"] or "")[:400])] += 1
    duplicates = sum(count - 1 for count in signatures.values() if count > 1)

    test_calls = [c for c in tool_calls if TEST_COMMAND.search(c["text"] or "")]
    write_calls = [c for c in tool_calls if WRITE_TOOL.search(c["name"] or "")]
    unverified_writes = 0
    if write_calls:
        last_test = max((c["seq"] for c in test_calls), default=-1)
        unverified_writes = sum(1 for c in write_calls if c["seq"] > last_test)

    blob = " ".join((e["text"] or "") for e in events).lower()
    referenced = sorted({name for name in available if name.lower() in blob})

    return {
        "user_turns": user_turns,
        "tool_calls": len(tool_calls),
        "tool_calls_per_turn": round(len(tool_calls) / user_turns, 2) if user_turns else 0.0,
        "errors": len(errors),
        "error_ratio": round(len(errors) / len(tool_calls), 3) if tool_calls else 0.0,
        "duplicate_calls": duplicates,
        "duplicate_ratio": round(duplicates / len(tool_calls), 3) if tool_calls else 0.0,
        "test_commands": len(test_calls),
        "write_calls": len(write_calls),
        "unverified_writes": unverified_writes,
        "skills_referenced": referenced,
    }


def rubric(score: dict) -> dict:
    """Three 0-100 sub-scores. Deterministic and documented, so a regression in
    the agent setup shows up as a number that moved, not as a feeling."""
    efficiency = 100.0
    efficiency -= min(60.0, score["duplicate_ratio"] * 200)
    efficiency -= min(20.0, max(0.0, score["tool_calls_per_turn"] - 3) * 5)
    efficiency -= min(20.0, score["error_ratio"] * 100)

    quality = 100.0
    quality -= min(50.0, score["unverified_writes"] * 15)
    if score["write_calls"] and not score["test_commands"]:
        quality -= 30.0
    quality -= min(20.0, score["error_ratio"] * 60)

    coverage = 100.0 if score["skills_referenced"] else 40.0
    coverage -= min(40.0, score["errors"] * 4)

    clamp = lambda value: round(max(0.0, min(100.0, value)), 1)  # noqa: E731
    return {"efficiency": clamp(efficiency), "quality": clamp(quality), "coverage": clamp(coverage)}


def score_corpus(db: sqlite3.Connection, available: list[str]) -> dict:
    sessions = db.execute("SELECT * FROM sessions ORDER BY started_at").fetchall()
    per_session = []
    usage = Counter()
    for session in sessions:
        events = load_events(db, session["session_id"])
        if not events:
            continue
        score = score_session(events, available)
        usage.update(score["skills_referenced"])
        per_session.append({
            "session_id": session["session_id"],
            "source": session["source"],
            "started_at": session["started_at"],
            "cwd": session["cwd"],
            **score,
            "rubric": rubric(score),
        })

    unused = [name for name in available if usage.get(name, 0) == 0]
    return {
        "sessions": len(per_session),
        "total_events": db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "skill_usage": dict(usage.most_common()),
        "unused_skills": unused,
        "available_skills": len(available),
        "per_session": per_session,
        "aggregate": aggregate(per_session),
    }


def aggregate(per_session: list[dict]) -> dict:
    if not per_session:
        return {"efficiency": 0.0, "quality": 0.0, "coverage": 0.0, "overall": 0.0}
    keys = ("efficiency", "quality", "coverage")
    means = {key: round(sum(s["rubric"][key] for s in per_session) / len(per_session), 1) for key in keys}
    means["overall"] = round(sum(means.values()) / len(keys), 1)
    means["unverified_writes"] = sum(s["unverified_writes"] for s in per_session)
    means["duplicate_calls"] = sum(s["duplicate_calls"] for s in per_session)
    means["errors"] = sum(s["errors"] for s in per_session)
    means["tool_calls"] = sum(s["tool_calls"] for s in per_session)
    return means


# --------------------------------------------------------------- proposals

RULES = (
    {
        "id": "duplicate-commands",
        "when": lambda agg, scored: agg["duplicate_calls"] >= 3,
        "target": "q-delegate-context",
        "section": "M5 (Validation and Acceptance)",
        "finding": "The same tool call was repeated {duplicate_calls} times across {sessions} sessions, "
                   "which means the coordinator retried an identical action instead of re-reading the result.",
        "edit": "Add a no-blind-retry gate: before repeating a command identical to a previous one in the "
                "same task, the executor must quote the prior output and state what changed.",
    },
    {
        "id": "unverified-writes",
        "when": lambda agg, scored: agg["unverified_writes"] >= 1,
        "target": "q-ci-fixer",
        "section": "Verification gate",
        "finding": "{unverified_writes} file-writing tool calls came after the last test command in their "
                   "session, so the edit was never exercised.",
        "edit": "Require a terminal evidence gate: no write is accepted until a test or reproduction "
                "command runs after it, with the command and its result quoted in the report.",
    },
    {
        "id": "error-rate",
        "when": lambda agg, scored: agg["errors"] >= 3,
        "target": "q-agent",
        "section": "Pre-flight",
        "finding": "{errors} tool errors were recorded across {sessions} sessions.",
        "edit": "Add a pre-flight checklist entry that probes the tool, credential or path before the "
                "first attempt, instead of discovering the failure mid-task.",
    },
    {
        "id": "skill-coverage",
        "when": lambda agg, scored: len(scored["unused_skills"]) > (scored["available_skills"] / 2),
        "target": "<consolidation>",
        "section": "frontmatter triggers",
        "finding": "{unused} of {available} installed skills were never referenced in any ingested session.",
        "edit": "Either the trigger text is not discoverable, or the skill duplicates another one. Rewrite "
                "the first 57 characters of the description as a self-contained trigger, or delete it.",
    },
)


def build_proposals(scored: dict) -> list[dict]:
    aggregate_scores = scored["aggregate"]
    if not scored["sessions"]:
        return []
    context = {
        "duplicate_calls": aggregate_scores["duplicate_calls"],
        "unverified_writes": aggregate_scores["unverified_writes"],
        "errors": aggregate_scores["errors"],
        "sessions": scored["sessions"],
        "unused": len(scored["unused_skills"]),
        "available": scored["available_skills"],
    }
    proposals = []
    for rule in RULES:
        if not rule["when"](aggregate_scores, scored):
            continue
        proposal = {
            "id": rule["id"],
            "target_skill": rule["target"],
            "section": rule["section"],
            "finding": rule["finding"].format(**context),
            "proposed_edit": rule["edit"].format(**context),
            "evidence": {
                "sessions": scored["sessions"],
                "session_ids": [s["session_id"] for s in scored["per_session"][:5]],
                "aggregate": aggregate_scores,
            },
            "handoff": "Apply with q-improve-loop. Do not edit the skill from this tool.",
        }
        proposals.append(proposal)
    return proposals


def write_proposals(proposals: list[dict], out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    written = []
    for proposal in proposals:
        path = out_dir / f"{stamp}-{proposal['id']}.md"
        path.write_text(render_proposal(proposal))
        written.append(str(path))
    return written


def render_proposal(proposal: dict) -> str:
    evidence = proposal["evidence"]["aggregate"]
    return "\n".join([
        f"# Skill Doctor proposal: {proposal['id']}",
        "",
        f"- Target skill: `{proposal['target_skill']}`",
        f"- Target section: {proposal['section']}",
        f"- Sessions scored: {proposal['evidence']['sessions']}",
        f"- Efficiency / Quality / Coverage: "
        f"{evidence['efficiency']} / {evidence['quality']} / {evidence['coverage']}",
        "",
        "## Finding",
        proposal["finding"],
        "",
        "## Proposed edit",
        proposal["proposed_edit"],
        "",
        "## Evidence",
        "Session ids: " + ", ".join(proposal["evidence"]["session_ids"]),
        "",
        "## Handoff",
        proposal["handoff"],
        "",
    ])


# --------------------------------------------------------------- CLI


def default_corpus(root: Path) -> Path:
    return root / ".q-agent" / "skill-doctor" / "corpus.db"


def ingest(root: Path, db: sqlite3.Connection, only: str, limit: int) -> dict:
    home = rel_home()
    counts = Counter()
    if only in ("all", "codex"):
        for path in sorted(home.joinpath(".codex/sessions").rglob("*.jsonl"))[-limit:]:
            meta, events = adapt_codex(path)
            if events:
                store(db, meta, events)
                counts["codex"] += 1
    if only in ("all", "agy"):
        for path in sorted(home.joinpath(".gemini/antigravity-cli/brain").rglob("transcript.jsonl"))[-limit:]:
            meta, events = adapt_antigravity(path)
            if events:
                store(db, meta, events)
                counts["agy"] += 1
    if only in ("all", "opencode"):
        for meta, events in adapt_opencode(home / ".local/share/opencode/opencode.db", limit=limit):
            if events:
                store(db, meta, events)
                counts["opencode"] += 1
    if only not in ("all", "codex", "agy", "opencode"):
        explicit = Path(only).expanduser()
        if not explicit.exists():
            raise SystemExit(f"refused: no such transcript source {only!r}")
        paths = [explicit] if explicit.is_file() else sorted(explicit.rglob("*.jsonl"))[-limit:]
        for path in paths:
            meta, events = adapt_jsonl(path)
            if events:
                store(db, meta, events)
                counts["jsonl"] += 1
    return {"ingested": dict(counts), "corpus": str(default_corpus(root))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score agent conversations and propose skill improvements")
    parser.add_argument("--root", default=".", help="q-agent package root")
    parser.add_argument("--corpus", help="override the corpus database path")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="read local transcripts into the corpus")
    p.add_argument("--source", default="all", help="all | codex | agy | opencode | <path to jsonl dir>")
    p.add_argument("--limit", type=int, default=25)

    sub.add_parser("score", help="score the corpus")
    p = sub.add_parser("report", help="write proposals for the findings")
    p.add_argument("--out", default=".q-agent/skill-doctor/proposals")
    sub.add_parser("status", help="corpus summary")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    corpus = Path(args.corpus) if args.corpus else default_corpus(root)
    db = connect(corpus)
    try:
        if args.command == "ingest":
            result = ingest(root, db, args.source, args.limit)
        else:
            scored = score_corpus(db, skill_names(root))
            if args.command == "score":
                result = {"aggregate": scored["aggregate"], "sessions": scored["sessions"],
                          "skill_usage": scored["skill_usage"], "unused_skills": scored["unused_skills"]}
            elif args.command == "status":
                result = {"corpus": str(corpus), "sessions": scored["sessions"],
                          "events": scored["total_events"], "aggregate": scored["aggregate"]}
            else:
                proposals = build_proposals(scored)
                written = write_proposals(proposals, Path(args.out))
                result = {"proposals": proposals, "written": written, "aggregate": scored["aggregate"]}
    finally:
        db.close()

    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
