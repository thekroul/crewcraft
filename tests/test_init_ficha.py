import os
import tempfile
import unittest
from pathlib import Path

from scripts.init_ficha import init_ficha, init_variant

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


class InitFichaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def project(self, *parts):
        path = self.base.joinpath(*parts)
        path.mkdir(parents=True)
        return path

    def test_creates_three_files(self):
        project = self.project("app")
        created = init_ficha(project, TEMPLATES)
        names = sorted(p.name for p in created)
        self.assertEqual(names, ["decisoes.md", "ficha-visual.md", "perguntas.md"])
        for path in created:
            self.assertTrue(path.is_file())
            self.assertEqual(path.parent, project / ".crewcraft")

    def test_does_not_copy_user_profile(self):
        project = self.project("app")
        init_ficha(project, TEMPLATES)
        self.assertFalse((project / ".crewcraft" / "perfil-usuario.md").exists())

    def test_does_not_overwrite_edited_file(self):
        project = self.project("app")
        (project / ".crewcraft").mkdir()
        edited = project / ".crewcraft" / "decisoes.md"
        edited.write_text("owner edit", encoding="utf-8")
        created = init_ficha(project, TEMPLATES)
        self.assertEqual(edited.read_text(encoding="utf-8"), "owner edit")
        self.assertEqual(sorted(p.name for p in created), ["ficha-visual.md", "perguntas.md"])

    def test_second_run_creates_nothing(self):
        project = self.project("app")
        init_ficha(project, TEMPLATES)
        self.assertEqual(init_ficha(project, TEMPLATES), [])

    def test_works_with_spaces_and_accents(self):
        project = self.project("My Projects", "extensão")
        created = init_ficha(project, TEMPLATES)
        self.assertEqual(len(created), 3)

    def test_refuses_nao_mexer_path(self):
        project = self.project("Não mexer", "docs")
        with self.assertRaises(ValueError):
            init_ficha(project, TEMPLATES)
        self.assertFalse((project / ".crewcraft").exists())

    def test_refuses_nao_mexer_without_accent_and_any_case(self):
        project = self.project("NAO MEXER", "docs")
        with self.assertRaises(ValueError):
            init_ficha(project, TEMPLATES)

    def test_relative_path_inside_nao_mexer_refused(self):
        inside = self.project("Não mexer", "sub")
        old = os.getcwd()
        os.chdir(inside)
        try:
            for relative in [".", ".."]:
                with self.assertRaises(ValueError):
                    init_ficha(Path(relative), TEMPLATES)
        finally:
            os.chdir(old)
        self.assertFalse((inside / ".crewcraft").exists())

    def test_variant_created_from_template(self):
        project = self.project("app")
        created = init_variant(project, "cliente-a", TEMPLATES)
        self.assertEqual([p.relative_to(project).as_posix() for p in created],
                         [".crewcraft/variantes/cliente-a/ficha-visual.md"])
        self.assertIn("only what differs", created[0].read_text(encoding="utf-8").lower())

    def test_variant_not_overwritten(self):
        project = self.project("app")
        first = init_variant(project, "cliente-a", TEMPLATES)[0]
        first.write_text("owner edit", encoding="utf-8")
        self.assertEqual(init_variant(project, "cliente-a", TEMPLATES), [])
        self.assertEqual(first.read_text(encoding="utf-8"), "owner edit")

    def test_variant_name_must_be_a_plain_name(self):
        project = self.project("app")
        for bad in ["", "..", "../x", "a/b", "a\\b", "."]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                init_variant(project, bad, TEMPLATES)

    def test_variant_refuses_nao_mexer(self):
        project = self.project("Nao Mexer", "docs")
        with self.assertRaises(ValueError):
            init_variant(project, "cliente-a", TEMPLATES)

    def test_missing_project_folder_raises(self):
        with self.assertRaises(FileNotFoundError):
            init_ficha(self.base / "does-not-exist", TEMPLATES)
        self.assertFalse((self.base / "does-not-exist").exists())


if __name__ == "__main__":
    unittest.main()
