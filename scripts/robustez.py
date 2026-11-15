"""Robustness checks, proportional to the project's operation profile.

Usage: python scripts/robustez.py <absolute project folder> <command>
  init-profile                         create .crewcraft/operacao.md to fill in (never overwrites)
  validate-profile                     is the profile complete and sensible?
  init                                 derive the required checks into .crewcraft/testes.md (keeps history)
  record <id> <passed|failed|waived> "<evidence>" [--by name]   (only "owner" may waive)
  status                               counts
  problems                             what still blocks a release (exit 1 if anything)
A calculator (local, no data, one user) needs two checks; a public system with money needs nineteen.
"""
import re
import sys
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project, _copy_if_missing
except ImportError:  # run as a plain script
    from init_ficha import _checked_project, _copy_if_missing

LABELS = {"users": "Users expected (typical)", "peak": "Users at the same time (peak)",
          "stress": "Stress target (concurrent users to test)", "exposure": "Exposure", "security": "Security level",
          "data": "Data handled", "availability": "Availability need", "cost": "Cost of a failure"}
ENUMS = {"exposure": {"local", "internal", "public-ip"}, "security": {"medium", "robust"},
         "data": {"none", "personal", "financial"}, "availability": {"best-effort", "business-hours", "always-on"}}
NUMBERS = ("users", "peak", "stress")
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "operacao.md"
STATUSES = ("pending", "passed", "failed", "waived")
HEADER = ("# Robustness checks\n\nEvery check the operation profile requires before a release. status: pending, passed, failed "
          "or waived (only the owner can waive). Change rows with scripts/robustez.py.\n\n"
          "| id | role | check | status | evidence | by |\n|---|---|---|---|---|---|\n")


def parse_profile(text) -> dict:
    result = {}
    for key, label in LABELS.items():
        match = re.search(rf"(?m)^- \*\*{re.escape(label)}:\*\*[ \t]*(.*)$", text)
        value = match.group(1).strip() if match else ""
        result[key] = int(value) if key in NUMBERS and value.isdigit() else value
    return result


def validate_profile(text) -> list:
    p, problems = parse_profile(text), []
    for key in NUMBERS:
        if not isinstance(p[key], int) or p[key] < 1:
            problems.append(f"{LABELS[key]}: a whole number of 1 or more")
    for key, allowed in ENUMS.items():
        if p[key] not in allowed:
            problems.append(f"{LABELS[key]}: one of {', '.join(sorted(allowed))}")
    if len(str(p["cost"])) < 3:
        problems.append(f"{LABELS['cost']}: say it in a sentence")
    if all(isinstance(p[k], int) for k in ("peak", "stress")) and p["stress"] < p["peak"]:
        problems.append(f"{LABELS['stress']}: must be at least the peak ({p['peak']})")
    return problems


def required_checks(p) -> list:
    peak, stress = int(p["peak"]), int(p["stress"])
    robust, exposure, data, availability = p["security"] == "robust", p["exposure"], p["data"], p["availability"]
    out = [("V1", "Dev", "Input validation: empty, very large, unicode, wrong type and repeated input"),
           ("V2", "QA", "Functional variations: normal, boundary, invalid and out-of-order actions")]
    if exposure != "local" or data != "none" or peak > 1:
        out += [("V3", "QA", "Failure paths: a dependency is down, a timeout, a full disk, bad configuration"),
                ("V4", "Dev", "Support-ready log and diagnostic package are present"),
                ("S1", "Security", "Secrets scan: no key, password or token in code, configuration or history"),
                ("S2", "Security", "Dependencies audited for known vulnerabilities")]
    if exposure != "local" or data != "none":
        out += [("S3", "Security", "Injection tests on every input: SQL, command, template, script (XSS) and path traversal"),
                ("S4", "Security", "Authentication, session and permission tests: another user's data, expired session, privilege escalation")]
    if robust:
        out.append(("S5", "Security", "Abuse and denial-of-service resistance: rate limits, oversized requests, repeated failures"))
        if data != "none":
            out.append(("S6", "Security", "Personal or financial data never appears in logs or error messages"))
        if exposure == "public-ip":
            out.append(("S7", "Security", "Transport encryption and security headers"))
    if peak > 1:
        out += [("C1", "QA", "Concurrent users: two people changing the same data, race conditions"),
                ("L1", "QA", f"Load test at the stress target ({stress} users at the same time): response times and error rate recorded")]
        if robust or exposure == "public-ip":
            out.append(("L2", "QA", f"Stress at 2x the target ({2 * stress} users) until it degrades: it must degrade gracefully and recover"))
        if availability == "always-on" or robust:
            out.append(("L3", "QA", "Soak test: steady load for at least one hour, looking for leaks and slowdowns"))
    if availability == "always-on":
        out += [("A1", "QA", "Restart and recovery: it comes back after a crash and the data is intact"),
                ("A2", "Dev", "Backup and restore were actually tested")]
    if data == "financial":
        out += [("F1", "QA", "Money calculations: rounding, currency, duplicates; retries are idempotent"),
                ("F2", "Security", "Audit trail: who changed what and when")]
    return [{"id": i, "role": r, "title": t} for i, r, t in out]


def _paths(project: Path):
    return project / ".crewcraft" / "operacao.md", project / ".crewcraft" / "testes.md"


def _read_matrix(path: Path) -> list:
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cells) >= 6 and cells[0] not in ("id",) and not set(cells[0]) <= {"-"}:
                rows.append(dict(zip(("id", "role", "title", "status", "evidence", "by"), cells)))
    return rows


def _write_matrix(path: Path, rows) -> None:
    body = "".join("| " + " | ".join(str(r[k]).replace("|", "/") for k in ("id", "role", "title", "status", "evidence", "by")) + " |\n" for r in rows)
    path.write_text(HEADER + body, encoding="utf-8")


def init_profile(project) -> bool:
    project = _checked_project(Path(project))
    (project / ".crewcraft").mkdir(exist_ok=True)
    return _copy_if_missing(TEMPLATE, _paths(project)[0])


def init_matrix(project) -> list:
    project = _checked_project(Path(project))
    profile_path, matrix_path = _paths(project)
    if not profile_path.is_file():
        raise ValueError("operation profile missing: run init-profile and fill it in")
    issues = validate_profile(profile_path.read_text(encoding="utf-8"))
    if issues:
        raise ValueError("operation profile incomplete: " + "; ".join(issues))
    rows = _read_matrix(matrix_path)
    have = {r["id"] for r in rows}
    for check in required_checks(parse_profile(profile_path.read_text(encoding="utf-8"))):
        if check["id"] not in have:
            rows.append({**check, "status": "pending", "evidence": "", "by": ""})
    _write_matrix(matrix_path, rows)
    return rows


def record(project, check_id, state, evidence, by):
    project = _checked_project(Path(project))
    if state not in ("passed", "failed", "waived"):
        raise ValueError("status must be passed, failed or waived")
    if not str(evidence).strip():
        raise ValueError("evidence is required: the command and its real result, or the reason")
    if state == "waived" and by != "owner":
        raise ValueError("only the owner can waive a check")
    _, matrix_path = _paths(project)
    rows = _read_matrix(matrix_path)
    row = next((r for r in rows if r["id"] == check_id), None)
    if row is None:
        raise ValueError(f"unknown check: {check_id}")
    row.update(status=state, evidence=str(evidence).strip(), by=by)
    _write_matrix(matrix_path, rows)
    return row


def status(project) -> dict:
    rows = _read_matrix(_paths(Path(project))[1])
    return {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}


def problems(project) -> list:
    profile_path, matrix_path = _paths(Path(project))
    if not profile_path.is_file():
        return ["operation profile missing: answer users, exposure, security level and stress target (.crewcraft/operacao.md)"]
    text = profile_path.read_text(encoding="utf-8")
    issues = validate_profile(text)
    if issues:
        return ["operation profile incomplete: " + "; ".join(issues)]
    if not matrix_path.is_file():
        return ["robustness checks not created yet: run robustez.py init"]
    rows = {r["id"]: r for r in _read_matrix(matrix_path)}
    out = []
    for check in required_checks(parse_profile(text)):
        row = rows.get(check["id"])
        state = row["status"] if row else "missing"
        if state not in ("passed", "waived"):
            out.append(f"{check['id']} ({check['role']}) {state}: {check['title']}")
    return out


def main(argv) -> int:
    args = list(argv[1:])
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        project, command, rest = _checked_project(Path(args[0])), args[1], args[2:]
        if command == "init-profile":
            print("created operacao.md: fill it in" if init_profile(project) else "operacao.md already exists")
        elif command == "validate-profile":
            path = _paths(project)[0]
            issues = validate_profile(path.read_text(encoding="utf-8")) if path.is_file() else ["operation profile missing"]
            print("\n".join(issues) if issues else "OK")
            return 1 if issues else 0
        elif command == "init":
            print(f"{len(init_matrix(project))} checks in testes.md")
        elif command == "record":
            by = "unknown"
            if "--by" in rest:
                i = rest.index("--by")
                by = rest[i + 1]
                del rest[i:i + 2]
            row = record(project, rest[0], rest[1], rest[2] if len(rest) > 2 else "", by)
            print(f"{row['id']} {row['status']}")
        elif command == "status":
            print(", ".join(f"{k} {v}" for k, v in status(project).items()))
        elif command == "problems":
            issues = problems(project)
            print("\n".join(issues) if issues else "OK: every required check passed or was waived by the owner")
            return 1 if issues else 0
        else:
            print(f"unknown command: {command}")
            return 2
        return 0
    except (ValueError, FileNotFoundError, IndexError) as error:
        print(error if not isinstance(error, IndexError) else "missing argument")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
