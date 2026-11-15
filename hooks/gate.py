"""Release gate (PreToolUse hook for Bash).

Blocks release commands (git push, publish, deploy...) in a project that has a Crewcraft
queue, until every Dev/Design/QA/Security task is approved and the owner's final test is
recorded. Projects without a queue are left alone. Any error lets the command through
(fail open), so a broken hook never traps the user.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if payload.get("tool_name") != "Bash":
            return 0
        from fila import is_release_command, load, owner_ok, release_problems
        from robustez import problems as robust_problems
        if not is_release_command(payload.get("tool_input", {}).get("command", "")):
            return 0
        start = Path(payload.get("cwd") or os.getcwd()).resolve()
        for folder in [start, *start.parents]:
            if (folder / ".crewcraft" / "fila.md").is_file():
                problems = release_problems(load(folder), owner_ok(folder)) + robust_problems(folder)
                if problems:
                    sys.stderr.write("Release blocked by Crewcraft. Still missing:\n- " + "\n- ".join(problems) +
                                     "\nExplain this to the owner in plain words and offer the next step.\n")
                    return 2
                return 0
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
