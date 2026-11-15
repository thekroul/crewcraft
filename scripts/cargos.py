"""Project roles: add as many specialists as the project needs, beyond the core crew.

Usage: python scripts/cargos.py <absolute project folder> <command>
  add "<name>" --mission "<what this role does>" [--reviewed yes|no]
  list
  validate
A new role gets a row in .crewcraft/cargos.md and its own agent in <project>/.claude/agents/.
There is no limit on the number of roles. Reviewed roles are checked by crewcraft:supervisor-geral;
roles that are not reviewed close their tasks with `finish`.
"""
import re
import sys
import unicodedata
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from init_ficha import _checked_project

CORE = ["Dev", "Design", "QA", "Security", "Support", "Marketing"]
CORE_REVIEWED = ["Dev", "Design", "QA", "Security"]
RESERVED = {"dev", "design", "qa", "security", "support", "marketing", "researcher",
            "supervisor-dev", "supervisor-design", "supervisor-teste", "supervisor-geral"}
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "cargo-agente.md"
TOOLS = "Read, Glob, Grep, Edit, Write, Bash"
HEADER = ("# Project roles\n\nSpecialists added for this project beyond the core crew. reviewed: yes means "
          "crewcraft:supervisor-geral must approve the role's work.\n\n| role | mission | reviewed | agent |\n|---|---|---|---|\n")
NAME = re.compile(r"[^\W_]+(?:[ \-][^\W_]+)*")


def slug(name: str) -> str:
    plain = "".join(c for c in unicodedata.normalize("NFD", name) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def _path(project: Path) -> Path:
    return project / ".crewcraft" / "cargos.md"


def load(project) -> list:
    path = _path(Path(project))
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cells) >= 4 and cells[0] != "role" and not set(cells[0]) <= {"-"}:
                rows.append({"role": cells[0], "mission": cells[1], "reviewed": cells[2].lower() == "yes", "agent": cells[3]})
    return rows


def role_names(project) -> list:
    return CORE + [r["role"] for r in load(project)]


def reviewed_roles(project) -> list:
    return CORE_REVIEWED + [r["role"] for r in load(project) if r["reviewed"]]


def add_role(project, name, mission, reviewed=True, tools=TOOLS) -> dict:
    project = _checked_project(Path(project))
    name, mission = " ".join(str(name).split()), " ".join(str(mission).split())
    if not (2 <= len(name) <= 30 and NAME.fullmatch(name)):
        raise ValueError("role name: 2 to 30 letters or digits, words separated by a space or a hyphen")
    key = slug(name)
    if key in RESERVED or name.lower() in {c.lower() for c in CORE}:
        raise ValueError(f"{name} is a core role: choose another name")
    if any(r["role"].lower() == name.lower() or slug(r["role"]) == key for r in load(project)):
        raise ValueError(f"role already exists: {name}")
    if len(mission) < 10:
        raise ValueError("mission: say in a sentence what this role does for the project")
    closing = ("`submit <id>`. You do not approve your own work: `crewcraft:supervisor-geral` reviews it."
               if reviewed else "close the task with `finish <id>` and a note of what you did and the evidence. This role has no supervisor.")
    description = f"The {name} role of this project's crew. {mission}".replace('"', "'").replace(chr(92), "/")
    agent = project / ".claude" / "agents" / f"{key}.md"
    agent.parent.mkdir(parents=True, exist_ok=True)
    if not agent.exists():
        text = (TEMPLATE.read_text(encoding="utf-8").replace("{slug}", key).replace("{name}", name)
                .replace("{description}", description).replace("{mission}", mission).replace("{tools}", tools).replace("{closing}", closing))
        agent.write_text(text, encoding="utf-8")
    path = _path(project)
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(HEADER, encoding="utf-8")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"| {name} | {mission.replace('|', '/')} | {'yes' if reviewed else 'no'} | {key} |\n")
    return {"role": name, "agent": str(agent), "reviewed": reviewed}


def validate_roles(project) -> list:
    problems = []
    for row in load(project):
        agent = Path(project) / ".claude" / "agents" / f"{row['agent']}.md"
        if not agent.is_file():
            problems.append(f"{row['role']}: agent file missing ({agent.name})")
            continue
        text = agent.read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10))
        match = re.match(chr(94) + "---" + chr(10) + "(.*?)" + chr(10) + "---" + chr(10), text, re.DOTALL)
        if not match:
            problems.append(f"{row['role']}: agent file has no header")
            continue
        try:
            import yaml
            data = yaml.safe_load(match.group(1)) or {}
        except ImportError:
            continue
        except Exception as exc:
            problems.append(f"{row['role']}: header is not valid YAML ({str(exc).splitlines()[0]})")
            continue
        if data.get("name") != row["agent"] or not data.get("description"):
            problems.append(f"{row['role']}: header needs name '{row['agent']}' and a description")
    return problems


def main(argv) -> int:
    args = list(argv[1:])
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        project, command, rest = _checked_project(Path(args[0])), args[1], args[2:]
        if command == "add":
            opts = {}
            for flag in ("--mission", "--reviewed"):
                if flag in rest:
                    i = rest.index(flag)
                    opts[flag] = rest[i + 1]
                    del rest[i:i + 2]
            made = add_role(project, rest[0], opts.get("--mission", ""), opts.get("--reviewed", "yes").lower() != "no")
            print(f"role {made['role']} added; agent: {made['agent']}")
        elif command == "list":
            for name in CORE:
                print(f"{name} (core)")
            for row in load(project):
                print(f"{row['role']}: {row['mission']} ({'reviewed' if row['reviewed'] else 'no review'})")
        elif command == "validate":
            problems = validate_roles(project)
            print("\n".join(problems) if problems else "OK")
            return 1 if problems else 0
        else:
            print(f"unknown command: {command}")
            return 2
        return 0
    except (ValueError, FileNotFoundError, IndexError) as error:
        print(error if not isinstance(error, IndexError) else "missing argument")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
