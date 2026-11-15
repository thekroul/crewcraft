"""Roadmap and phase documents.

Usage: python scripts/plano.py <absolute project folder> validate
The roadmap (.crewcraft/plano.md) is an illustration of the project: one entry per phase and the owner's
choice of where to stop. Every phase has its own document in .crewcraft/fases/ with its architecture and
the executable points of each role. `validate` checks the roadmap and every phase document it names.
"""
import re
import sys
from pathlib import Path

try:
    from scripts.cargos import role_names
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from cargos import role_names
    from init_ficha import _checked_project

SECTIONS = ["Goal", "Architecture", "Executable points", "Variations to test", "Security and load checks", "Needs"]
DOCUMENT = re.compile(r"fases/\d{2}-[a-z0-9\-]+\.md")


def validate_plano(text) -> list:
    blocks = re.split(r"(?m)^(?=## Phase )", text.replace("\r\n", "\n"))[1:]
    if not blocks:
        return ["no phases: add at least one '## Phase N: name'"]
    problems, numbers = [], []
    for block in blocks:
        head = block.splitlines()[0]
        match = re.match(r"## Phase (\d+): (.+)$", head)
        if not match:
            problems.append(f"{head[3:].strip()}: the heading must look like '## Phase 1: name'")
            continue
        numbers.append(int(match.group(1)))
        title = head[3:].strip()
        summary = re.search(r"(?m)^\*\*Summary:\*\*[ \t]*(.*)$", block)
        if not summary or not summary.group(1).strip():
            problems.append(f"{title}: Summary is missing or empty")
        document = re.search(r"(?m)^\*\*Document:\*\*[ \t]*(.*)$", block)
        if not document or not DOCUMENT.fullmatch(document.group(1).strip()):
            problems.append(f"{title}: Document must look like fases/01-name.md")
    stop = re.search(r"(?m)^\*\*Stop after:\*\*[ \t]*(.*)$", text)
    value = stop.group(1).strip().lower() if stop else ""
    if not value:
        problems.append("Stop after is missing: write 'all' or 'phases 5, 12' (the owner's choice)")
    elif value != "all":
        match = re.fullmatch(r"phases?\s+(\d+(?:\s*,\s*\d+)*)", value)
        if not match:
            problems.append("Stop after must be 'all' or 'phases 5, 12'")
        else:
            unknown = [n for n in (int(x) for x in re.split(r"\s*,\s*", match.group(1))) if n not in numbers]
            if unknown:
                problems.append(f"Stop after names phases that do not exist: {unknown}")
    return problems


def validate_fase(text, roles=None) -> list:
    text = text.replace("\r\n", "\n")
    problems = []
    for name in SECTIONS:
        match = re.search(rf"(?ms)^## {re.escape(name)}[ \t]*\n(.*?)(?=^## |\Z)", text)
        if not match:
            problems.append(f"missing section: {name}")
            continue
        body = match.group(1).strip()
        if name == "Executable points":
            rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in body.splitlines() if line.startswith("|")]
            rows = [r for r in rows[1:] if not set("".join(r)) <= set("-: ")]
            if not rows:
                problems.append("Executable points: add at least one row (role | point | deliverable | acceptance test)")
            for cells in rows:
                if len(cells) < 4 or not all(cells[:4]):
                    problems.append(f"Executable points: incomplete row for {cells[0] if cells else '?'}")
                elif roles and cells[0] not in roles:
                    problems.append(f"Executable points: unknown role {cells[0]}")
        elif not body:
            problems.append(f"{name} is empty")
    if "## Sign-off" not in text:
        problems.append("missing section: Sign-off")
    return problems


def main(argv) -> int:
    if len(argv) < 3 or argv[2] != "validate":
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(argv[1]))
        text = (project / ".crewcraft" / "plano.md").read_text(encoding="utf-8")
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    problems = validate_plano(text)
    roles = role_names(project)
    for document in dict.fromkeys(re.findall(r"(?m)^\*\*Document:\*\*[ \t]*(\S+)", text)):
        path = project / ".crewcraft" / document
        if not path.is_file():
            problems.append(f"{document}: the phase document does not exist")
        else:
            problems += [f"{document}: {p}" for p in validate_fase(path.read_text(encoding="utf-8"), roles)]
    print("\n".join(problems) if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
