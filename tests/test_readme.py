import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READMES = {"en": ROOT / "README.md", "pt": ROOT / "README.pt-BR.md"}
IMAGES = ["conversa.png", "estruturas.png", "temas.png"]


def text(lang):
    return READMES[lang].read_text(encoding="utf-8")


class ReadmeTests(unittest.TestCase):
    def test_both_languages_exist(self):
        for path in READMES.values():
            self.assertTrue(path.is_file(), path)

    def test_every_skill_and_command_is_documented_in_both(self):
        skills = [p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")]
        commands = [p.stem for p in (ROOT / "commands").glob("*.md")]
        self.assertTrue(skills and commands)
        for lang in READMES:
            for name in skills:
                self.assertIn(f"`{name}`", text(lang), f"{lang}: skill {name}")
            for name in commands:
                self.assertIn(f"/crewcraft:{name}", text(lang), f"{lang}: command {name}")

    def test_images_exist_and_are_used_with_alt_text_in_both(self):
        for lang in READMES:
            for image in IMAGES:
                self.assertTrue((ROOT / "docs" / "img" / image).is_file(), image)
                match = re.search(rf"!\[([^\]]+)\]\(docs/img/{re.escape(image)}\)", text(lang))
                self.assertIsNotNone(match, f"{lang}: {image} needs alt text")

    def test_same_structure_in_both_languages(self):
        headings = {lang: len(re.findall(r"(?m)^## ", text(lang))) for lang in READMES}
        self.assertEqual(headings["en"], headings["pt"])
        self.assertGreaterEqual(headings["en"], 6)

    def test_cross_links_and_install_commands(self):
        self.assertIn("README.pt-BR.md", text("en"))
        self.assertIn("README.md", text("pt"))
        for lang in READMES:
            self.assertIn("/plugin marketplace add", text(lang))
            self.assertIn("/plugin install crewcraft@crewcraft", text(lang))

    def test_privacy_statement_present(self):
        self.assertIn(".crewcraft", text("en"))
        self.assertIn(".crewcraft", text("pt"))


if __name__ == "__main__":
    unittest.main()
