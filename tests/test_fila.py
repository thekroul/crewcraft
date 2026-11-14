import json
import tempfile
import unittest
from pathlib import Path

from scripts.fila import (Task, add, approve, finish, load, main, next_task, parse, placar,
                          serialize, set_priority, start, submit, validate)


def t(id, role="Dev", priority="Normal", needs=(), status="todo", note="", title=None):
    return Task(id=id, title=title or f"task {id}", role=role, priority=priority,
                needs=list(needs), status=status, by="manager", note=note)


class QueueRulesTests(unittest.TestCase):
    def test_roundtrip_keeps_every_field(self):
        tasks = [t("T1", status="done", note="tests green"), t("T2", needs=["T1"], priority="High")]
        self.assertEqual(parse(serialize(tasks)), tasks)

    def test_next_respects_dependencies(self):
        tasks = [t("T1"), t("T2", needs=["T1"])]
        self.assertEqual(next_task(tasks, "Dev").id, "T1")
        tasks[0].status = "done"
        self.assertEqual(next_task(tasks, "Dev").id, "T2")

    def test_next_orders_by_priority_then_arrival(self):
        tasks = [t("T1", priority="Low"), t("T2", priority="High"), t("T3", priority="High"), t("T4")]
        self.assertEqual(next_task(tasks, "Dev").id, "T2")

    def test_busy_role_gets_nothing(self):
        tasks = [t("T1", status="doing"), t("T2")]
        self.assertIsNone(next_task(tasks, "Dev"))

    def test_only_tasks_of_that_role(self):
        tasks = [t("T1", role="QA"), t("T2", role="Dev")]
        self.assertEqual(next_task(tasks, "QA").id, "T1")

    def test_urgent_stops_everything_else(self):
        tasks = [t("T1", role="Dev", priority="Urgent"), t("T2", role="QA")]
        self.assertIsNone(next_task(tasks, "QA"))
        self.assertEqual(next_task(tasks, "Dev").id, "T1")

    def test_start_urgent_pauses_the_others_and_finish_resumes_them(self):
        tasks = [t("T1", role="QA", status="doing"), t("T2", role="Dev", priority="Urgent")]
        start(tasks, "T2")
        self.assertEqual([x.status for x in tasks], ["paused", "doing"])
        self.assertIn("T2", tasks[0].note)
        submit(tasks, "T2")
        approve(tasks, "T2", "hotfix verified on a clean machine")
        self.assertEqual([x.status for x in tasks], ["doing", "done"])

    def test_raising_to_urgent_pauses_running_work_and_records_who(self):
        tasks = [t("T1", role="QA", status="doing"), t("T2", role="Dev")]
        set_priority(tasks, "T2", "Urgent", by="owner")
        self.assertEqual(tasks[0].status, "paused")
        self.assertEqual(tasks[1].by, "owner")

    def test_finish_needs_evidence(self):
        tasks = [t("T1", role="Support", status="doing")]
        with self.assertRaises(ValueError):
            finish(tasks, "T1", "  ")

    def test_cannot_start_a_task_whose_dependency_is_not_done(self):
        tasks = [t("T1"), t("T2", needs=["T1"])]
        with self.assertRaises(ValueError):
            start(tasks, "T2")

    def test_scoreboard_counts_only_tested_work(self):
        tasks = [t("T1", status="done", note="ok"), t("T2", status="doing"),
                 t("T3", status="paused", note="paused by T9"), t("T4")]
        score = placar(tasks)
        self.assertEqual((score["total"], score["done"], score["percent"]), (4, 1, 25))
        self.assertEqual([x["id"] for x in score["in_construction"]], ["T2", "T3"])

    def test_validate_catches_the_known_problems(self):
        problems = validate([
            t("T1", status="doing"), t("T2", status="doing"),          # two doing for one role
            t("T3", needs=["T99"]),                                     # unknown dependency
            t("T4", needs=["T5"]), t("T5", needs=["T4"]),              # cycle
            t("T6", role="Chef"), t("T7", priority="Huge"),            # unknown role / priority
            t("T8", status="blocked"),                                  # blocked without a reason
            t("T1", title="duplicate id"),
        ])
        text = " ".join(problems)
        for expected in ["two", "T99", "cycle", "Chef", "Huge", "T8", "duplicate"]:
            self.assertIn(expected, text, expected)

    def test_validate_accepts_a_clean_queue(self):
        self.assertEqual(validate([t("T1", status="done", note="ok"), t("T2", needs=["T1"])]), [])


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "My App"
        self.project.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        return main(["fila.py", str(self.project), *args])

    def test_full_flow_writes_queue_and_events(self):
        self.assertEqual(self.run_cli("init"), 0)
        self.assertEqual(self.run_cli("add", "Login screen", "Dev", "--priority", "High"), 0)
        self.assertEqual(self.run_cli("add", "Test login", "QA", "--needs", "T1"), 0)
        self.assertEqual(self.run_cli("start", "T1"), 0)
        self.assertEqual(self.run_cli("start", "T2"), 1)          # dependency not done
        self.assertEqual(self.run_cli("submit", "T1"), 0)
        self.assertEqual(self.run_cli("approve", "T1", "unit tests green", "--by", "supervisor-dev"), 0)
        self.assertEqual(self.run_cli("next", "QA"), 0)
        tasks = load(self.project)
        self.assertEqual([x.status for x in tasks], ["done", "todo"])
        events = [json.loads(l) for l in
                  (self.project / ".crewcraft" / "eventos.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["event"] for e in events], ["add", "add", "start", "submit", "approve"])
        self.assertTrue(all({"time", "role", "task"} <= set(e) for e in events))

    def test_init_does_not_overwrite_and_refuses_read_only_folder(self):
        self.run_cli("init")
        queue = self.project / ".crewcraft" / "fila.md"
        queue.write_text(queue.read_text(encoding="utf-8") + "\nowner note\n", encoding="utf-8")
        self.run_cli("init")
        self.assertIn("owner note", queue.read_text(encoding="utf-8"))
        locked = Path(self.tmp.name) / "Não mexer" / "x"
        locked.mkdir(parents=True)
        self.assertEqual(main(["fila.py", str(locked), "init"]), 1)
        self.assertFalse((locked / ".crewcraft").exists())


if __name__ == "__main__":
    unittest.main()
