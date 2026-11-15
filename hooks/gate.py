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
        from fila import is_release_command, load, owner_ok, release_problems, signoff_problems
        from robustez import problems as robust_problems
        from cargos import reviewed_roles
        if not is_release_command(payload.get("tool_input", {}).get("command", "")):
            return 0
        start = Path(payload.get("cwd") or os.getcwd()).resolve()
        for folder in [start, *start.parents]:
            if (folder / ".crewcraft" / "fila.md").is_file():
                committing = bool(__import__('re').search(r'\bgit\s+commit\b', payload.get('tool_input', {}).get('command', '')))
                final_test_done = owner_ok(folder) or committing  # a commit needs the signed delivery; push and deploy also need the owner's final test
                problems = release_problems(load(folder), final_test_done, reviewed_roles(folder)) + robust_problems(folder) + signoff_problems(folder)
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
