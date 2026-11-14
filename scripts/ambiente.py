"""Environment sheet: what this computer has, and what to use for each job.

Usage: python scripts/ambiente.py [--out <file>]
Detects installed tools (it installs nothing and sends nothing anywhere), then lists, for each
job, the options in order: what is ready first, each with its weakness in plain words and how
to get it. Save the result in the user's own Claude configuration folder, never in the plugin
or in a project.
"""
import os
import shutil
import sys
from pathlib import Path

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SANDBOX = r"C:\Windows\System32\WindowsSandbox.exe"


def detect(which=shutil.which, platform=sys.platform, exists=os.path.exists) -> dict:
    name = "windows" if platform.startswith("win") else "macos" if platform == "darwin" else "linux"
    caps = {"os": name, "python": sys.version.split()[0]}
    for tool in ["git", "node", "npm", "docker", "vboxmanage", "wsl", "adb", "firefox"]:
        caps[tool] = bool(which(tool))
    caps["edge"] = bool(which("msedge")) or bool(exists(EDGE))
    caps["chrome"] = bool(which("chrome") or which("google-chrome")) or bool(exists(CHROME))
    caps["windows_sandbox"] = name == "windows" and bool(exists(SANDBOX))
    return caps


def _o(name, available, weakness, how):
    return {"name": name, "available": bool(available), "weakness": weakness, "how_to_get": how}


def options(caps: dict) -> dict:
    vm = _o("Virtual machine", caps["vboxmanage"],
            "Heavy: uses a lot of disk and memory, needs a system installed inside it, and is slower.",
            "Install VirtualBox (or turn on Hyper-V on Windows Pro), then create a clean machine.")
    spare = _o("Another computer", False, "Needs a spare computer, and copying the build by hand.",
               "Use any spare PC and copy the build to it.")
    if caps["os"] == "windows":
        clean = [
            _o("Windows Sandbox", caps["windows_sandbox"],
               "Same Windows version as this PC, and it needs virtualization turned on.",
               "Turn on 'Windows Sandbox' in Windows Features (Windows Pro, with virtualization enabled in the BIOS)."),
            vm,
            _o("Second Windows user", True,
               "Uses the same Windows system files and components as your user, so it cannot catch a problem "
               "caused by a component that only this PC has.",
               "Settings, Accounts, Other users, add a new local user, then sign in as that user to test."),
            spare]
    elif caps["os"] == "macos":
        clean = [vm, _o("New user account", True,
                        "Shares the same system and tools as your account.", "System Settings, Users, add a user."),
                 spare]
    else:
        clean = [
            _o("Container", caps["docker"],
               "Shares this computer's kernel, so it cannot catch kernel or driver differences.",
               "Install Docker, then run the build in a fresh container."),
            vm,
            _o("New user account", True,
               "Shares the same system and installed libraries as your account.", "Create a new user and test as that user."),
            spare]
    browser = [
        _o("Playwright headless browser", caps["node"],
           "Downloads browsers the first time (needs internet once) and runs on this PC only.",
           "Install Node.js, then run: npx playwright install"),
        _o("Edge headless screenshots", caps["edge"], "Takes pictures only; it cannot click through the app.",
           "Install Microsoft Edge."),
        _o("Chrome headless screenshots", caps["chrome"], "Takes pictures only; it cannot click through the app.",
           "Install Google Chrome."),
        _o("Manual check by the owner", True, "Slow, and depends on the person doing it.",
           "The crew prepares a short step-by-step list to follow."),
    ]
    vcs = [_o("Git", caps["git"], "Needs a name and e-mail configured before the first commit.", "Install Git.")]

    def ordered(items):
        return [i for i in items if i["available"]] + [i for i in items if not i["available"]]

    return {"clean_test_environment": ordered(clean), "browser_check": ordered(browser), "version_control": ordered(vcs)}


def render(caps: dict, listing: dict) -> str:
    lines = ["# Environment sheet", "", f"Operating system: {caps['os']}. Python {caps['python']}.", ""]
    for job, items in listing.items():
        lines += [f"## {job.replace('_', ' ')}", ""]
        for item in items:
            mark = "x" if item["available"] else " "
            status = "ready" if item["available"] else "not available"
            lines.append(f"- [{mark}] **{item['name']}**: {status}. Weakness: {item['weakness']}")
            if not item["available"]:
                lines.append(f"  How to get it: {item['how_to_get']}")
        lines.append("")
    return "\n".join(lines)


def main(argv) -> int:
    caps = detect()
    text = render(caps, options(caps))
    args = list(argv[1:])
    if "--out" in args:
        Path(args[args.index("--out") + 1]).write_text(text, encoding="utf-8")
        print("environment sheet saved")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
