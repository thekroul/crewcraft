import json
import tempfile
import unittest
from pathlib import Path

from tools.check_plugin import check_plugin


def make_plugin(root, name="crewcraft", version="0.1.0",
                description="A team of specialists for Claude Code.", extra=None):
    (root / ".claude-plugin").mkdir(parents=True)
    data = {"name": name, "version": version, "description": description}
    if extra:
        data.update(extra)
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(data), encoding="utf-8")


def add_skill(root, folder, name, description):
    d = root / "skills" / folder
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# Body\n", encoding="utf-8")


class CheckPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_plugin_has_no_errors(self):
        make_plugin(self.root)
        add_skill(self.root, "conversa", "conversa", "Use when an owner describes something to build.")
        self.assertEqual(check_plugin(self.root), [])

    def test_missing_manifest_reported(self):
        self.assertTrue(any("plugin.json" in e for e in check_plugin(self.root)))

    def test_wrong_name_reported(self):
        make_plugin(self.root, name="other")
        self.assertTrue(any("name" in e for e in check_plugin(self.root)))

    def test_bad_version_reported(self):
        make_plugin(self.root, version="1.0")
        self.assertTrue(any("version" in e for e in check_plugin(self.root)))

    def test_skill_name_must_match_folder(self):
        make_plugin(self.root)
        add_skill(self.root, "conversa", "outra", "Use when something happens.")
        self.assertTrue(any("conversa" in e and "name" in e for e in check_plugin(self.root)))

    def test_description_must_start_with_use_when(self):
        make_plugin(self.root)
        add_skill(self.root, "conversa", "conversa", "Talks to people.")
        self.assertTrue(any("Use when" in e for e in check_plugin(self.root)))

    def test_author_email_rejected(self):
        make_plugin(self.root, extra={"author": {"name": "X", "email": "x@example.com"}})
        self.assertTrue(any("author" in e for e in check_plugin(self.root)))

    def test_command_needs_description(self):
        make_plugin(self.root)
        (self.root / "commands").mkdir()
        (self.root / "commands" / "comecar.md").write_text("Load the skill.\n", encoding="utf-8")
        self.assertTrue(any("comecar" in e and "description" in e for e in check_plugin(self.root)))


def add_marketplace(root, plugins, owner=None):
    data = {"name": "crewcraft", "owner": owner or {"name": "Crewcraft"}, "plugins": plugins}
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(data), encoding="utf-8")


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_plugin(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_marketplace_has_no_errors(self):
        add_marketplace(self.root, [{"name": "crewcraft", "source": "./", "description": "x"}])
        self.assertEqual(check_plugin(self.root), [])

    def test_marketplace_must_list_crewcraft(self):
        add_marketplace(self.root, [])
        self.assertTrue(any("marketplace" in e and "crewcraft" in e for e in check_plugin(self.root)))

    def test_marketplace_source_must_be_repo_root(self):
        add_marketplace(self.root, [{"name": "crewcraft", "source": "./elsewhere"}])
        self.assertTrue(any("source" in e for e in check_plugin(self.root)))

    def test_marketplace_owner_email_rejected(self):
        add_marketplace(self.root, [{"name": "crewcraft", "source": "./"}],
                        owner={"name": "X", "email": "x@example.com"})
        self.assertTrue(any("owner" in e for e in check_plugin(self.root)))


if __name__ == "__main__":
    unittest.main()
