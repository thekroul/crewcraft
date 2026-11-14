import unittest

from scripts.ambiente import detect, options, render


def which_of(*found):
    return lambda name: f"/bin/{name}" if name in found else None


def win(found=("git", "node"), sandbox=False):
    return detect(which=which_of(*found), platform="win32",
                  exists=lambda p: sandbox and p.endswith("WindowsSandbox.exe"))


class EnvironmentTests(unittest.TestCase):
    def test_detects_tools_and_sandbox(self):
        caps = win(sandbox=True)
        self.assertEqual(caps["os"], "windows")
        self.assertTrue(caps["git"] and caps["node"] and caps["windows_sandbox"])
        self.assertFalse(caps["docker"])

    def test_best_available_clean_environment_comes_first(self):
        first = options(win(sandbox=True))["clean_test_environment"][0]
        self.assertEqual((first["name"], first["available"]), ("Windows Sandbox", True))

    def test_without_sandbox_a_second_user_is_the_fallback_with_its_weakness_explained(self):
        listing = options(win(sandbox=False))["clean_test_environment"]
        first = listing[0]
        self.assertEqual((first["name"], first["available"]), ("Second Windows user", True))
        self.assertIn("same", first["weakness"].lower())
        sandbox = next(o for o in listing if o["name"] == "Windows Sandbox")
        self.assertFalse(sandbox["available"])
        self.assertTrue(sandbox["how_to_get"])

    def test_every_option_has_a_weakness_and_a_way_to_get_it(self):
        for listing in options(win()).values():
            for option in listing:
                self.assertTrue(option["weakness"] and option["how_to_get"], option["name"])

    def test_linux_has_its_own_options(self):
        caps = detect(which=which_of("git", "docker"), platform="linux", exists=lambda p: False)
        names = [o["name"] for o in options(caps)["clean_test_environment"]]
        self.assertEqual(names[0], "Container")
        self.assertNotIn("Windows Sandbox", names)

    def test_render_is_plain_markdown_without_personal_paths(self):
        text = render(win(sandbox=True), options(win(sandbox=True)))
        self.assertIn("Windows Sandbox", text)
        self.assertIn("weakness", text.lower())
        self.assertNotIn("Users", text)

    def test_browser_check_prefers_what_is_installed(self):
        caps = detect(which=which_of("node", "msedge"), platform="win32", exists=lambda p: False)
        first = options(caps)["browser_check"][0]
        self.assertTrue(first["available"])


if __name__ == "__main__":
    unittest.main()
