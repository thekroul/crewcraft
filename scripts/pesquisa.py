"""Research helper: keeps outside searches generic, logs them, and checks the report.

Usage: python scripts/pesquisa.py <absolute project folder> <command>
  check "<query>"            refuse queries that carry personal, client or project data
  log "<query>" "<source>"   check, then append to .crewcraft/buscas.md
  validate                   check .crewcraft/parecer.md (sources, dates, verdicts)
  outdated                   list report rows older than 18 months (exit 1 if any: time to refresh)
Private terms to keep out of searches: the project's folder name plus one per line in
.crewcraft/privado.txt (for example client names).
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
    from scripts.mask import mask
except ImportError:  # run as a plain script
    from init_ficha import _checked_project
    from mask import mask

VERDICTS = {"use", "improve", "avoid"}
SECTIONS = ["Summary", "Competitors", "Tools and skills", "Documentation", "Robustness and sizing", "Proposed crew", "Risks and questions", "Sources"]
TABLES = ["Competitors", "Tools and skills", "Documentation", "Robustness and sizing"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOG_HEADER = ("# Searches\n\nEvery search made outside this computer for this project. Queries are generic: "
              "no client, project or personal data.\n\n| date | query | source |\n|---|---|---|\n")


def _private_terms(project: Path) -> list:
    terms = [project.name]
    path = project / ".crewcraft" / "privado.txt"
    if path.is_file():
        terms += [l.strip() for l in path.read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.lstrip().startswith("#")]
    return terms


def check_query(project, query) -> list:
    project = Path(project)
    problems = []
    if mask(query) != query:
        problems.append("contains personal or client data (id, e-mail, secret or user path)")
    if re.search(r"[A-Za-z]:[\\/]|\\\\|/Users/|/home/", query):
        problems.append("contains a file path")
    for term in _private_terms(project):
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", query, re.IGNORECASE):
            problems.append(f"contains a private term: {term}")
    return problems


def log_search(project, query, source, today=None):
    project = _checked_project(Path(project))
    problems = check_query(project, query)
    if problems:
        raise ValueError("search refused: " + "; ".join(problems))
    path = project / ".crewcraft" / "buscas.md"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        path.write_text(LOG_HEADER, encoding="utf-8")
    row = f"| {(today or date.today()).isoformat()} | {query.replace('|', '/')} | {source.replace('|', '/')} |\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(row)


def _rows(text):
    section, header = None, None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            section, header = line[3:].strip(), None
        elif line.startswith("|") and section in TABLES:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if header is None:
                header = [c.lower() for c in cells]
                continue
            yield section, dict(zip(header, cells))


def validate_parecer(text) -> list:
    problems = [f"missing section: {s}" for s in SECTIONS if f"## {s}" not in text]
    for section, row in _rows(text):
        name = next(iter(row.values()), "?")
        source, when = row.get("source", ""), row.get("date", "")
        if not ((source.startswith("http") and DATE.match(when)) or (source == "from memory" and when == "unverified")):
            problems.append(f"{name}: needs a source URL and a date (or 'from memory' with date 'unverified')")
        if section == "Tools and skills" and row.get("verdict", "").lower() not in VERDICTS:
            problems.append(f"{name}: verdict must be use, improve or avoid")
    return problems


def outdated(text, today=None, months=18) -> list:
    today = today or date.today()
    flagged = []
    for _, row in _rows(text):
        when = row.get("date", "")
        if DATE.match(when):
            age = (today - datetime.strptime(when, "%Y-%m-%d").date()).days
            if age > months * 30:
                flagged.append(next(iter(row.values())))
    return flagged


def main(argv) -> int:
    args = list(argv[1:])
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(args[0]))
        command, rest = args[1], args[2:]
        if command == "check":
            problems = check_query(project, rest[0])
            print("\n".join(problems) if problems else "OK: generic query")
            return 1 if problems else 0
        if command == "log":
            log_search(project, rest[0], rest[1] if len(rest) > 1 else "web search")
            print("search logged")
            return 0
        if command == "validate":
            text = (project / ".crewcraft" / "parecer.md").read_text(encoding="utf-8")
            problems = validate_parecer(text)
            if problems:
                print("\n".join(problems))
                return 1
            memory = sum(1 for _, r in _rows(text) if r.get("source") == "from memory")
            print(f"OK ({memory} from memory, {len(outdated(text))} possibly outdated)")
            return 0
        if command == "outdated":
            text = (project / ".crewcraft" / "parecer.md").read_text(encoding="utf-8")
            old = outdated(text)
            print("\n".join(f"{name}: older than 18 months, refresh it" for name in old) if old else "OK: nothing outdated")
            return 1 if old else 0
        print(f"unknown command: {command}")
        return 2
    except (ValueError, FileNotFoundError, IndexError) as error:
        print(error if not isinstance(error, IndexError) else "missing argument")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
