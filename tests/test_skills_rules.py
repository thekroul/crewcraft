import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class SkillRulesTests(unittest.TestCase):
    """Pins the written rules the review found missing. Behavior itself is proven by the scenarios."""

    def test_every_skill_that_writes_knows_the_read_only_folder_rule(self):
        for name in ["conversa", "ficha-do-projeto", "prototipo-visual"]:
            self.assertIn("Não mexer", skill(name), name)

    def test_skills_confirm_which_folder_is_the_project(self):
        for name in ["conversa", "ficha-do-projeto", "prototipo-visual"]:
            self.assertIn("which folder is the project", skill(name).lower(), name)

    def test_skills_never_claim_a_decision_is_saved_without_writing_it(self):
        self.assertIn("never say a decision is saved", skill("conversa").lower())

    def test_folder_confirmation_only_when_in_doubt(self):
        text = skill("conversa").lower()
        self.assertIn("without a separate question", text)
        self.assertIn("several separate projects", text)

    def test_manager_skill_rules(self):
        text = skill("gerente")
        lowered = text.lower()
        for needle in ["fila.py", "Urgent", "one task per role", "--by owner", "placar", "Não mexer",
                       "which folder is the project", "never writes product code", "evidence",
                       "when the owner reports a problem or declares something urgent"]:
            self.assertIn(needle.lower(), lowered, needle)

    def test_manager_dispatches_the_crew_and_guards_the_release(self):
        lowered = skill("gerente").lower()
        for needle in ["crewcraft:dev", "crewcraft:qa", "crewcraft:supervisor-dev", "crewcraft:supervisor-teste",
                       "release-check", "release-ok", "explicit yes", "plugin root", "three rejections"]:
            self.assertIn(needle, lowered, needle)

    def test_crew_agents_exist_and_supervisors_cannot_edit(self):
        for name in ["dev", "qa", "supervisor-dev", "supervisor-teste"]:
            self.assertTrue((ROOT / "agents" / f"{name}.md").is_file(), name)
        for name in ["supervisor-dev", "supervisor-teste"]:
            tools = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8").split("tools:", 1)[1].split("\n", 1)[0]
            self.assertNotIn("Edit", tools)
            self.assertNotIn("Write", tools)

    def test_design_security_and_marketing_roles(self):
        for name in ["design", "supervisor-design", "security", "marketing"]:
            self.assertTrue((ROOT / "agents" / f"{name}.md").is_file(), name)
        agent = lambda n: (ROOT / "agents" / f"{n}.md").read_text(encoding="utf-8").lower()
        self.assertIn("visual approved", agent("design"))
        self.assertIn("banned", agent("supervisor-design"))
        self.assertIn("only what already works", agent("marketing"))
        self.assertIn("finish", agent("marketing"))
        self.assertIn("never fix", agent("security"))
        tools = agent("supervisor-design").split("tools:", 1)[1].splitlines()[0]
        self.assertNotIn("edit", tools)
        self.assertNotIn("write", tools)

    def test_support_agent_masks_before_reading_and_proposes_priority(self):
        text = (ROOT / "agents" / "support.md").read_text(encoding="utf-8").lower()
        for needle in ["mask.py", "never read the original", "five parts", "normal", "propose", "plain words"]:
            self.assertIn(needle, text, needle)

    def test_environment_skill_rules(self):
        text = skill("ambiente").lower()
        for needle in ["ambiente.py", "approval", "never in the plugin", "weakness", "filename", "source", "size"]:
            self.assertIn(needle, text, needle)

    def test_manager_description_starts_with_use_when(self):
        self.assertTrue(skill("gerente").split("description:", 1)[1].lstrip().startswith("Use when"))

    def test_visual_skill_asks_one_question_at_a_time(self):
        self.assertIn("one question per message", skill("prototipo-visual").lower())

    def test_project_skill_describes_client_variants(self):
        text = skill("ficha-do-projeto")
        self.assertIn("variantes", text)
        self.assertIn("init_ficha.py", text)
        self.assertIn("--variant", text)

    def test_profile_permission_prompt_is_explained_to_the_person(self):
        self.assertIn("permission", skill("conversa").lower())

    def test_manifest_descriptions_do_not_promise_missing_features(self):
        for path in [ROOT / ".claude-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"]:
            text = path.read_text(encoding="utf-8").lower()
            self.assertIn("early version", text, path.name)
            for claim in ["researches", "ships only what was tested", "crew of specialist roles"]:
                self.assertNotIn(claim, text, f"{path.name}: {claim}")

    def test_readme_says_the_command_is_the_reliable_way_in(self):
        self.assertIn("not guaranteed", (ROOT / "README.md").read_text(encoding="utf-8").lower())
        self.assertIn("não é garantid", (ROOT / "README.pt-BR.md").read_text(encoding="utf-8").lower())

    def test_readme_does_not_overstate_the_read_only_rule(self):
        self.assertNotIn("The plugin refuses to write", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
