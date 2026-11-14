import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.fila import (Task, approve, finish, is_release_command, reject, release_problems,
                          serialize, submit)

ROOT = Path(__file__).resolve().parents[1]


def t(id, role="Dev", status="todo", note="", priority="Normal", tries=0):
    return Task(id=id, title=f"task {id}", role=role, priority=priority, needs=[], status=status,
                by="manager", note=note, tries=tries)


class ReviewFlowTests(unittest.TestCase):
    def test_submit_moves_doing_to_review_and_nothing_else(self):
        tasks = [t("T1", status="doing"), t("T2")]
        submit(tasks, "T1")
        self.assertEqual(tasks[0].status, "review")
        with self.assertRaises(ValueError):
            submit(tasks, "T2")

    def test_approve_needs_review_status_and_evidence(self):
        tasks = [t("T1", status="review")]
        with self.assertRaises(ValueError):
            approve(tasks, "T1", " ")
        approve(tasks, "T1", "tests green")
        self.assertEqual((tasks[0].status, tasks[0].note), ("done", "tests green"))
        with self.assertRaises(ValueError):
            approve([t("T2", status="doing")], "T2", "x")

    def test_reviewed_roles_cannot_skip_review_with_finish(self):
        with self.assertRaises(ValueError):
            finish([t("T1", role="Dev", status="doing")], "T1", "tested")
        done = finish([t("T2", role="Support", status="doing")], "T2", "tested")
        self.assertEqual(done.status, "done")

    def test_reject_returns_work_with_reason_and_higher_priority(self):
        tasks = [t("T1", status="review")]
        reject(tasks, "T1", "login fails on empty password")
        self.assertEqual((tasks[0].status, tasks[0].priority, tasks[0].tries), ("todo", "High", 1))
        self.assertIn("empty password", tasks[0].note)

    def test_third_rejection_goes_to_the_owner(self):
        tasks = [t("T1", status="review", tries=2)]
        reject(tasks, "T1", "still broken")
        self.assertEqual(tasks[0].status, "blocked")
        self.assertIn("owner", tasks[0].note.lower())

    def test_tries_survive_the_file(self):
        from scripts.fila import parse
        tasks = [t("T1", tries=2)]
        self.assertEqual(parse(serialize(tasks))[0].tries, 2)


class ReleaseGateTests(unittest.TestCase):
    def clean(self):
        return [t("T1", "Dev", "done", "ok"), t("T2", "QA", "done", "ok"), t("T3", "Security", "done", "ok")]

    def test_clean_queue_with_owner_ok_may_release(self):
        self.assertEqual(release_problems(self.clean(), owner_ok=True), [])

    def test_each_problem_is_reported(self):
        tasks = [t("T1", "Dev", "review"), t("T2", "QA", "done", "ok")]
        text = " ".join(release_problems(tasks, owner_ok=False))
        for expected in ["T1", "Security", "owner"]:
            self.assertIn(expected, text, expected)

    def test_marketing_and_support_do_not_block(self):
        tasks = self.clean() + [t("T4", "Marketing", "todo"), t("T5", "Support", "doing")]
        self.assertEqual(release_problems(tasks, owner_ok=True), [])

    def test_release_commands_are_recognised(self):
        for cmd in ["git push origin main", "npm publish", "gh release create v1", "docker push x/y",
                    "cargo publish", "twine upload dist/*", "npx wrangler deploy", "git tag v1.0"]:
            self.assertTrue(is_release_command(cmd), cmd)
        for cmd in ["git status", "npm test", "python -m unittest", "git commit -m x", "git log"]:
            self.assertFalse(is_release_command(cmd), cmd)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "My App"
        (self.project / ".crewcraft").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, command, tool="Bash"):
        payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}, "cwd": str(self.project)})
        return subprocess.run([sys.executable, str(ROOT / "hooks" / "gate.py")], input=payload,
                              capture_output=True, text=True, encoding="utf-8")

    def write_queue(self, tasks):
        (self.project / ".crewcraft" / "fila.md").write_text(serialize(tasks), encoding="utf-8")

    def test_project_without_a_queue_is_left_alone(self):
        self.assertEqual(self.run_hook("git push").returncode, 0)

    def test_incomplete_queue_blocks_a_release_with_the_reasons(self):
        self.write_queue([t("T1", "Dev", "review")])
        result = self.run_hook("git push origin main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("T1", result.stderr)

    def test_ordinary_commands_and_other_tools_pass(self):
        self.write_queue([t("T1", "Dev", "review")])
        self.assertEqual(self.run_hook("git status").returncode, 0)
        self.assertEqual(self.run_hook("git push", tool="Read").returncode, 0)

    def test_complete_queue_and_owner_ok_pass(self):
        self.write_queue([t("T1", "Dev", "done", "ok"), t("T2", "QA", "done", "ok"), t("T3", "Security", "done", "ok")])
        self.assertEqual(self.run_hook("git push").returncode, 2)
        (self.project / ".crewcraft" / "liberacao.json").write_text(json.dumps({"owner_ok": True}), encoding="utf-8")
        self.assertEqual(self.run_hook("git push").returncode, 0)

    def test_broken_input_fails_open(self):
        result = subprocess.run([sys.executable, str(ROOT / "hooks" / "gate.py")], input="not json",
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
