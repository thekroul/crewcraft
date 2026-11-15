"""Step documents: every stage of the plan says what to create, how, what is delivered and how it is tested.

Usage: python scripts/plano.py <absolute project folder> validate
Checks .crewcraft/plano.md: at least one "## Stage N: name", each with the seven labelled, non-empty fields (write "none: reason" when a check does not apply).
"""
import re
import sys
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from init_ficha import _checked_project

FIELDS = ["What to create", "How", "Deliverable", "Acceptance test", "Variations to test", "Security and load checks", "Needs"]


def validate_plano(text) -> list:
    blocks = re.split(r"(?m)^(?=## Stage)", text.replace("\r\n", "\n"))[1:]
    if not blocks:
        return ["no stages: add at least one '## Stage N: name'"]
    problems = []
    for block in blocks:
        title = block.splitlines()[0][3:].strip()
        for field in FIELDS:
            match = re.search(rf"(?m)^\*\*{re.escape(field)}:\*\*[ \t]*(.*)$", block)
            if not match:
                problems.append(f"{title}: missing '{field}'")
            elif not match.group(1).strip():
                problems.append(f"{title}: '{field}' is empty")
    return problems


def main(argv) -> int:
    if len(argv) < 3 or argv[2] != "validate":
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(argv[1]))
        problems = validate_plano((project / ".crewcraft" / "plano.md").read_text(encoding="utf-8"))
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    print("\n".join(problems) if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
