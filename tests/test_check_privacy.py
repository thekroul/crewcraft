import tempfile
import unittest
from pathlib import Path

from tools.check_privacy import check_privacy


class CheckPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_windows_user_path_flagged(self):
        self.write("a.md", "line one\nsee C:\\Users\\Someone\\file.txt\n")
        errors = check_privacy(self.root, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("a.md:2", errors[0])

    def test_email_flagged(self):
        self.write("a.md", "contact: someone@example.com\n")
        self.assertEqual(len(check_privacy(self.root, [])), 1)

    def test_secret_assignment_flagged(self):
        self.write("a.json", '{"api_key": "abc123"}\n')
        self.assertEqual(len(check_privacy(self.root, [])), 1)

    def test_private_term_flagged_case_insensitive(self):
        self.write("a.md", "built for the Acme client\n")
        errors = check_privacy(self.root, ["acme"])
        self.assertEqual(len(errors), 1)
        self.assertIn("private term", errors[0])

    def test_private_term_matches_whole_words_only(self):
        self.write("a.py", "harbors = load()\n")
        self.assertEqual(check_privacy(self.root, ["harbor"]), [])

    def test_multiword_private_term_flagged(self):
        self.write("a.md", "kept in the Blue Harbor folder\n")
        self.assertEqual(len(check_privacy(self.root, ["Blue Harbor"])), 1)

    def test_private_term_flagged_inside_tests_and_tools_too(self):
        self.write("tests/t.py", "fixture = 'Blue Harbor'\n")
        self.write("tools/x.py", "# Blue Harbor\n")
        self.assertEqual(len(check_privacy(self.root, ["blue harbor"])), 2)

    def test_results_folder_is_skipped_for_private_terms(self):
        self.write("tests/scenarios/results/out.txt", "Blue Harbor\n")
        self.assertEqual(check_privacy(self.root, ["blue harbor"]), [])

    def test_clean_file_passes(self):
        self.write("a.md", "A crew of specialist roles.\n")
        self.assertEqual(check_privacy(self.root, ["acme"]), [])

    def test_tools_and_tests_folders_are_skipped(self):
        self.write("tools/x.py", "C:\\Users\\Someone\\\n")
        self.write("tests/x.py", "someone@example.com\n")
        self.assertEqual(check_privacy(self.root, []), [])


if __name__ == "__main__":
    unittest.main()
