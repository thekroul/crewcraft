import tempfile
import unittest
from pathlib import Path

from tools.check_originality import check_originality, shingles

BORROWED = (
    "Always ask the owner one question at a time before building anything "
    "because a wrong guess costs far more than a short question ever will."
)


class ShinglesTests(unittest.TestCase):
    def test_shingles_normalise_case_and_punctuation(self):
        result = shingles("A b, C d. e f g H i", n=8)
        self.assertEqual(len(result), 2)
        self.assertIn(("a", "b", "c", "d", "e", "f", "g", "h"), result)


class CheckOriginalityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "plugin"
        self.corpus = base / "corpus"
        self.root.mkdir()
        self.corpus.mkdir()
        (self.corpus / "other.md").write_text("Intro text.\n" + BORROWED + "\nOutro.\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_copied_paragraph_flagged(self):
        (self.root / "SKILL.md").write_text("My notes. " + BORROWED + "\n", encoding="utf-8")
        errors = check_originality(self.root, self.corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("SKILL.md", errors[0])
        self.assertIn("other.md", errors[0])

    def test_original_text_passes(self):
        (self.root / "SKILL.md").write_text(
            "Before any code exists, talk with the owner, note each choice, and show a mockup first.\n",
            encoding="utf-8")
        self.assertEqual(check_originality(self.root, self.corpus), [])


if __name__ == "__main__":
    unittest.main()
