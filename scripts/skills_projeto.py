"""Project skills: a few small skills that belong to ONE project, plus its managed CLAUDE.md block.

Usage: python scripts/skills_projeto.py <absolute project folder> <command>
  init <name>   create <project>/.claude/skills/<name>/SKILL.md from the skeleton (never overwrites)
  validate      check every project skill (lean, aligned with decisions, sourced and dated)
  claude-md     create or refresh the Crewcraft block in the project's CLAUDE.md (the rest is untouched)
"""
import re
import sys
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from init_ficha import _checked_project

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_LINES = 120
SKELETON = Path(__file__).resolve().parents[1] / "templates" / "skill-projeto.md"
BLOCK = """<!-- crewcraft:start -->
## Crewcraft (managed block: edit outside the markers)
- Decisions live in `.crewcraft/decisoes.md`; questions in `.crewcraft/perguntas.md`; the research report in `.crewcraft/parecer.md`; the plan in `.crewcraft/plano.md`; the queue in `.crewcraft/fila.md`. Read them before working.
- Skills for this project are in `.claude/skills/`; use only those that apply.
- Order of work: conversation, research, the look, the plan, the work, the release. Ask before assuming, one question per message.
- Never write inside a folder the owner listed as read-only.
<!-- crewcraft:end -->
"""


def init_skill(project, name) -> list:
    if not NAME.match(name or ""):
        raise ValueError(f"skill name must be lowercase words joined by '-': {name!r}")
    project = _checked_project(Path(project))
    path = project / ".claude" / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as handle:
            handle.write(SKELETON.read_text(encoding="utf-8").replace("{name}", name))
    except FileExistsError:
        return []
    return [path]


def _front(text):
    match = re.match(r"^---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.DOTALL)
    fields = {}
    for line in (match.group(1).split("\n") if match else []):
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def validate_project_skills(project) -> list:
    problems = []
    for path in sorted(Path(project).glob(".claude/skills/*/SKILL.md")):
        folder, text = path.parent.name, path.read_text(encoding="utf-8")
        fields = _front(text)
        if fields.get("name") != folder:
            problems.append(f"{folder}: name must equal the folder name")
        if not fields.get("description", "").startswith("Use when"):
            problems.append(f"{folder}: description must start with 'Use when'")
        if "TODO" in text:
            problems.append(f"{folder}: contains TODO, fill it in")
        if len(text.splitlines()) > MAX_LINES:
            problems.append(f"{folder}: too long ({len(text.splitlines())} lines, max {MAX_LINES})")
        if not re.search(r"(?m)^Aligned with:.*\bD\d+", text):
            problems.append(f"{folder}: needs an 'Aligned with:' line listing decision ids (D1, D2...)")
        if not re.search(r"(?m)^Sources:.*https?://\S+.*\d{4}-\d{2}-\d{2}", text):
            problems.append(f"{folder}: needs a 'Sources:' line with a URL and a date (YYYY-MM-DD)")
    return problems


def update_claude_md(project):
    project = _checked_project(Path(project))
    path = project / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(r"<!-- crewcraft:start -->.*?<!-- crewcraft:end -->\n?", re.DOTALL)
    text = pattern.sub(BLOCK, text) if pattern.search(text) else (text.rstrip() + "\n\n" if text.strip() else "") + BLOCK
    path.write_text(text, encoding="utf-8")
    return path


def main(argv) -> int:
    args = list(argv[1:])
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        project, command = Path(args[0]), args[1]
        if command == "init":
            made = init_skill(project, args[2] if len(args) > 2 else "")
            print(f"created {made[0]}" if made else "already exists")
            return 0
        if command == "validate":
            problems = validate_project_skills(_checked_project(project))
            print("\n".join(problems) if problems else "OK")
            return 1 if problems else 0
        if command == "claude-md":
            print(f"updated {update_claude_md(project)}")
            return 0
        print(f"unknown command: {command}")
        return 2
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
