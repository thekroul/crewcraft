import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from scripts.escritorio import build_state, make_server
from scripts.fila import Task, serialize

ROOT = Path(__file__).resolve().parents[1]


def t(id, role, status="todo", note="", title=None):
    return Task(id=id, title=title or f"task {id}", role=role, status=status, note=note)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "My App"
        (self.project / ".crewcraft").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def queue(self, tasks, events=()):
        (self.project / ".crewcraft" / "fila.md").write_text(serialize(tasks), encoding="utf-8")
        (self.project / ".crewcraft" / "eventos.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")

    def test_no_queue_means_an_empty_office(self):
        state = build_state(self.project)
        self.assertEqual((state["roles"], state["placar"]), ([], None))

    def test_one_entry_per_role_present_with_its_state_and_task(self):
        self.queue([t("T1", "Dev", "doing", title="Login screen"), t("T2", "QA", "review", title="Test login"),
                    t("T3", "Security", "blocked", "owner decision needed"), t("T4", "Design", "done", "ok"),
                    t("T5", "Dev", "todo")])
        by_role = {r["role"]: r for r in build_state(self.project)["roles"]}
        self.assertEqual(set(by_role), {"Dev", "Design", "QA", "Security"})
        self.assertEqual((by_role["Dev"]["state"], by_role["Dev"]["task"]), ("work", "Login screen"))
        self.assertEqual(by_role["QA"]["state"], "review")
        self.assertEqual(by_role["Security"]["state"], "blocked")
        self.assertEqual(by_role["Design"]["state"], "idle")

    def test_names_are_stable_and_scoreboard_is_honest(self):
        self.queue([t("T1", "Dev", "doing"), t("T2", "QA", "done", "ok")])
        state = build_state(self.project)
        self.assertEqual([r["name"] for r in state["roles"]], ["Ana", "Carla"])
        self.assertEqual((state["placar"]["done"], state["placar"]["total"], state["placar"]["percent"]), (1, 2, 50))

    def test_recent_events_are_included_last_first_limited(self):
        events = [{"time": f"2026-01-01T00:00:{i:02d}+00:00", "role": "Dev", "task": "T1", "event": "start"} for i in range(12)]
        self.queue([t("T1", "Dev", "doing")], events)
        got = build_state(self.project)["events"]
        self.assertEqual(len(got), 8)
        self.assertEqual(got[-1]["time"], "2026-01-01T00:00:11+00:00")


class ServerTests(unittest.TestCase):
    def test_serves_page_and_state_on_the_local_address_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "app"
            (project / ".crewcraft").mkdir(parents=True)
            (project / ".crewcraft" / "fila.md").write_text(serialize([t("T1", "Dev", "doing")]), encoding="utf-8")
            server = make_server(project, port=0)
            self.assertEqual(server.server_address[0], "127.0.0.1")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                page = urllib.request.urlopen(base + "/").read().decode("utf-8")
                self.assertIn("<canvas", page)
                state = json.loads(urllib.request.urlopen(base + "/state.json").read().decode("utf-8"))
                self.assertEqual(state["roles"][0]["state"], "work")
                with self.assertRaises(Exception):
                    urllib.request.urlopen(base + "/other")
            finally:
                server.shutdown()
                server.server_close()

    def test_page_template_talks_to_nobody_outside(self):
        page = (ROOT / "templates" / "escritorio" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)
        self.assertIn("state.json", page)


if __name__ == "__main__":
    unittest.main()
