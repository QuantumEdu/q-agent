"""
Unit tests for tools/q-skill-doctor/skill_doctor.py

Fixtures are synthetic: the doctor must not depend on the machine having any
particular set of agent transcripts to be testable.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCTOR_DIR = ROOT_DIR / "tools" / "q-skill-doctor"
if str(DOCTOR_DIR) not in sys.path:
    sys.path.insert(0, str(DOCTOR_DIR))

import skill_doctor


def codex_line(kind, payload, ts="2026-11-01T10:00:00Z"):
    return json.dumps({"timestamp": ts, "type": kind, "payload": payload})


class TestAdapters(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_codex_adapter_extracts_user_assistant_and_tool_calls(self):
        path = self.root / "rollout-test.jsonl"
        path.write_text("\n".join([
            codex_line("session_meta", {"session_id": "abc", "cwd": "/repo"}),
            codex_line("response_item", {"type": "message", "role": "user",
                                         "content": [{"type": "input_text", "text": "fix the test"}]}),
            codex_line("response_item", {"type": "custom_tool_call", "name": "exec",
                                         "input": "pytest -q", "status": "completed"}),
            codex_line("response_item", {"type": "message", "role": "assistant",
                                         "content": [{"type": "output_text", "text": "done"}]}),
        ]))
        meta, events = skill_doctor.adapt_codex(path)

        self.assertEqual(meta["session_id"], "abc")
        self.assertEqual(meta["cwd"], "/repo")
        kinds = [e["kind"] for e in events]
        self.assertEqual(kinds, ["user_message", "tool_call", "assistant_message"])
        self.assertEqual(events[1]["name"], "exec")

    def test_antigravity_adapter_reads_step_transcript(self):
        brain = self.root / "brain" / "uuid-1" / ".system_generated" / "logs"
        brain.mkdir(parents=True)
        path = brain / "transcript.jsonl"
        path.write_text("\n".join([
            json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "status": "DONE",
                        "step_index": 0, "content": "run the suite"}),
            json.dumps({"type": "PLANNER_RESPONSE", "source": "MODEL", "status": "DONE",
                        "step_index": 1, "content": "running", "tool_calls": [{"name": "run_command",
                                                                               "args": {"cmd": "just test"}}]}),
            json.dumps({"type": "GENERIC", "source": "MODEL", "status": "ERROR",
                        "step_index": 2, "content": "boom"}),
        ]))
        meta, events = skill_doctor.adapt_antigravity(path)

        self.assertEqual(meta["session_id"], "agy:uuid-1")
        self.assertEqual(meta["source"], "agy")
        kinds = [e["kind"] for e in events]
        self.assertIn("user_message", kinds)
        self.assertIn("tool_call", kinds)
        self.assertIn("error", kinds)

    def test_jsonl_adapter_is_role_agnostic(self):
        path = self.root / "custom.jsonl"
        path.write_text("\n".join([
            json.dumps({"role": "user", "content": "hello"}),
            json.dumps({"role": "assistant", "content": "hi"}),
            json.dumps({"kind": "tool_call", "name": "exec", "text": "ls"}),
        ]))
        meta, events = skill_doctor.adapt_jsonl(path)

        self.assertEqual(meta["source"], "jsonl")
        self.assertEqual([e["kind"] for e in events],
                         ["user_message", "assistant_message", "tool_call"])

    def test_malformed_lines_are_skipped(self):
        path = self.root / "broken.jsonl"
        path.write_text("not json\n" + json.dumps({"role": "user", "content": "ok"}))
        _, events = skill_doctor.adapt_jsonl(path)
        self.assertEqual(len(events), 1)


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db = skill_doctor.connect(Path(self.test_dir.name) / "corpus.db")

    def tearDown(self):
        self.db.close()
        self.test_dir.cleanup()

    def store(self, events, session_id="s1"):
        skill_doctor.store(
            self.db,
            {"session_id": session_id, "source": "test", "path": "/tmp/x"},
            events,
        )
        return skill_doctor.load_events(self.db, session_id)

    def test_duplicate_tool_calls_are_counted(self):
        rows = self.store([
            {"kind": "user_message", "role": "user", "text": "go"},
            {"kind": "tool_call", "name": "exec", "text": "git status"},
            {"kind": "tool_call", "name": "exec", "text": "git status"},
            {"kind": "tool_call", "name": "exec", "text": "git status"},
        ])
        score = skill_doctor.score_session(rows, [])
        self.assertEqual(score["duplicate_calls"], 2)
        self.assertLess(skill_doctor.rubric(score)["efficiency"], 100.0)

    def test_writes_after_the_last_test_are_unverified(self):
        rows = self.store([
            {"kind": "tool_call", "name": "exec", "text": "pytest -q"},
            {"kind": "tool_call", "name": "write_file", "text": "src/app.py"},
            {"kind": "tool_call", "name": "patch", "text": "src/app.py"},
        ])
        score = skill_doctor.score_session(rows, [])
        self.assertEqual(score["write_calls"], 2)
        self.assertEqual(score["unverified_writes"], 2)

    def test_a_write_followed_by_a_test_is_verified(self):
        rows = self.store([
            {"kind": "tool_call", "name": "write_file", "text": "src/app.py"},
            {"kind": "tool_call", "name": "exec", "text": "go test ./..."},
        ])
        score = skill_doctor.score_session(rows, [])
        self.assertEqual(score["unverified_writes"], 0)
        self.assertEqual(score["test_commands"], 1)

    def test_skill_references_are_detected(self):
        rows = self.store([
            {"kind": "assistant_message", "role": "assistant",
             "text": "I will use q-delegate-context for this"},
        ])
        score = skill_doctor.score_session(rows, ["q-delegate-context", "q-ci-fixer"])
        self.assertEqual(score["skills_referenced"], ["q-delegate-context"])

    def test_rubric_is_bounded(self):
        worst = skill_doctor.rubric({
            "user_turns": 1, "tool_calls": 10, "tool_calls_per_turn": 10.0,
            "errors": 40, "error_ratio": 4.0, "duplicate_calls": 9,
            "duplicate_ratio": 0.9, "test_commands": 0, "write_calls": 9,
            "unverified_writes": 9, "skills_referenced": [],
        })
        for value in worst.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 100.0)

    def test_corpus_scoring_and_proposals(self):
        self.store([
            {"kind": "user_message", "role": "user", "text": "go"},
            {"kind": "tool_call", "name": "write_file", "text": "src/app.py"},
        ], session_id="s1")
        scored = skill_doctor.score_corpus(self.db, ["q-agent"])

        self.assertEqual(scored["sessions"], 1)
        self.assertEqual(scored["aggregate"]["unverified_writes"], 1)
        self.assertIn("q-agent", scored["unused_skills"])

        proposals = skill_doctor.build_proposals(scored)
        self.assertTrue(any(p["id"] == "unverified-writes" for p in proposals))
        for proposal in proposals:
            self.assertIn("evidence", proposal)
            self.assertIn("session_ids", proposal["evidence"])

    def test_proposals_are_written_as_drafts_not_applied(self):
        self.store([
            {"kind": "user_message", "role": "user", "text": "go"},
            {"kind": "tool_call", "name": "write_file", "text": "src/app.py"},
        ])
        scored = skill_doctor.score_corpus(self.db, ["q-agent"])
        proposals = skill_doctor.build_proposals(scored)

        with tempfile.TemporaryDirectory() as out:
            written = skill_doctor.write_proposals(proposals, Path(out))
            self.assertTrue(written)
            content = Path(written[0]).read_text()
            self.assertIn("# Skill Doctor proposal", content)
            self.assertIn("q-improve-loop", content)

    def test_empty_corpus_produces_no_proposals(self):
        scored = skill_doctor.score_corpus(self.db, ["q-agent"])
        self.assertEqual(scored["sessions"], 0)
        self.assertEqual(skill_doctor.build_proposals(scored), [])


if __name__ == "__main__":
    unittest.main()
