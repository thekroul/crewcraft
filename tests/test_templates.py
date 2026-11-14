import re
import unittest
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
TOKENS = ["--bg", "--surface", "--text", "--accent", "--accent-2", "--border"]


def read(*parts):
    return (TEMPLATES.joinpath(*parts)).read_text(encoding="utf-8")


class TemplateTests(unittest.TestCase):
    def test_profile_template_has_all_areas(self):
        text = read("perfil-usuario.md")
        for area in ["development", "design", "security", "infrastructure", "ai", "language"]:
            self.assertRegex(text, rf"(?m)^{area}:", area)
        for level in ["novice", "intermediate", "expert"]:
            self.assertIn(level, text)

    def test_decisions_table_columns(self):
        text = read("decisoes.md")
        self.assertIn("| id | decision | by | date |", text)
        self.assertIn("owner", text)
        self.assertIn("suggestion", text)

    def test_questions_table_columns(self):
        self.assertIn("| id | question | status | answer |", read("perguntas.md"))

    def test_banned_list_present(self):
        text = read("ficha-visual.md").lower()
        self.assertIn("banned (ai look)", text)
        for keyword in ["gradient", "frosted", "rounded", "glow", "emoji", "round placeholder numbers"]:
            self.assertIn(keyword, text, keyword)
        for section in ["palette", "typography", "density", "shape", "reference qualities"]:
            self.assertIn(section, text, section)

    def test_base_html_has_no_hardcoded_colors(self):
        html = read("mockup", "base.html")
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", html))
        self.assertIsNone(re.search(r"\b(?:rgb|rgba|hsl|hsla)\(", html))
        self.assertIn("var(--bg)", html)

    def test_base_html_links_exactly_one_theme(self):
        html = read("mockup", "base.html")
        self.assertEqual(len(re.findall(r'href="theme-[a-z]+\.css"', html)), 1)

    def test_both_themes_define_all_tokens_without_gradients(self):
        for name in ["theme-neutral.css", "theme-warm.css"]:
            css = read("mockup", name)
            for token in TOKENS:
                self.assertRegex(css, rf"{re.escape(token)}\s*:", f"{name} {token}")
            self.assertNotIn("gradient(", css.lower(), name)

    def test_themes_are_different(self):
        self.assertNotEqual(read("mockup", "theme-neutral.css"), read("mockup", "theme-warm.css"))


if __name__ == "__main__":
    unittest.main()
