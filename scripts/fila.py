"""Task queue with priorities for the crew (one task per role at a time).

Usage: python scripts/fila.py <absolute project folder> <command> [args]
  init                                  create .crewcraft/fila.md (never overwrites)
  add "<task>" <role> [--priority P] [--needs T1,T2] [--by manager|owner]
  next <role>                           what that role should do now
  start <id>                            a role starts a task
  submit <id>                           the role hands its work to the supervisor
  approve <id> "<evidence>" [--by name] supervisor: done and tested
  reject <id> "<reason>" [--by name]    back to the role (3rd time: asks the owner)
  finish <id> "<evidence>"              Support and Marketing only (no supervisor)
  sign <qa|security|test|manager> "<evidence>" [--by name]   the four signatures of the delivery
  release-check / release-ok "<note>"   release gate / the owner said yes
  priority <id> <Urgent|High|Normal|Low> --by manager|owner
  placar                                honest scoreboard
  validate                              check the queue rules
Every change appends a line to .crewcraft/eventos.jsonl.
"""
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project, _copy_if_missing
except ImportError:  # run as a plain script
    from init_ficha import _checked_project, _copy_if_missing

ROLES = ["Dev", "Design", "QA", "Security", "Support", "Marketing"]
PRIORITIES = {"Urgent": 0, "High": 1, "Normal": 2, "Low": 3}
STATUSES = ["todo", "doing", "review", "paused", "blocked", "done"]
REVIEWED = ["Dev", "Design", "QA", "Security"]  # their work needs a supervisor before it counts
WHO = ["manager", "owner"]
HEADER = ("# Queue\n\nOne task per role at a time. Priorities: Urgent (stops everything), High, Normal, Low. "
          "`done` means built AND tested; the note then holds the evidence. Edit rows only.\n\n"
          "| id | task | role | priority | needs | status | by | note | tries |\n|---|---|---|---|---|---|---|---|---|\n")


@dataclass
class Task:
    id: str
    title: str
    role: str
    priority: str = "Normal"
    needs: list = field(default_factory=list)
    status: str = "todo"
    by: str = "manager"
    note: str = ""
    tries: int = 0


def serialize(tasks) -> str:
    rows = []
    for x in tasks:
        cells = [x.id, x.title, x.role, x.priority, ", ".join(x.needs) or "-", x.status, x.by, x.note, x.tries]
        rows.append("| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |")
    return HEADER + "\n".join(rows) + ("\n" if rows else "")


def parse(text: str) -> list:
    tasks = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] == "id" or set(cells[0]) <= {"-"}:
            continue
        cells += [""] * (9 - len(cells))
        needs = [n.strip() for n in cells[4].split(",") if n.strip() and n.strip() != "-"]
        tasks.append(Task(cells[0], cells[1], cells[2], cells[3], needs, cells[5], cells[6], cells[7],
                          int(cells[8]) if cells[8].isdigit() else 0))
    return tasks


def _find(tasks, task_id):
    for x in tasks:
        if x.id == task_id:
            return x
    raise ValueError(f"unknown task: {task_id}")


def _deps_done(tasks, task) -> bool:
    return all(_find(tasks, n).status == "done" for n in task.needs if any(y.id == n for y in tasks))


def _open_urgent(tasks):
    return [x for x in tasks if x.priority == "Urgent" and x.status != "done"]


def _pause_others(tasks, urgent_id):
    for x in tasks:
        if x.id != urgent_id and x.status == "doing":
            x.status, x.note = "paused", f"paused by {urgent_id}"


def _resume_if_clear(tasks):
    if _open_urgent(tasks):
        return
    for x in tasks:
        if x.status == "paused" and x.note.startswith("paused by"):
            x.status, x.note = "doing", ""


def next_task(tasks, role):
    if any(x.role == role and x.status == "doing" for x in tasks):
        return None
    pool = [x for x in tasks if x.role == role and x.status == "todo" and _deps_done(tasks, x)]
    if _open_urgent(tasks):
        pool = [x for x in pool if x.priority == "Urgent"]
    order = {id(x): i for i, x in enumerate(tasks)}
    pool.sort(key=lambda x: (PRIORITIES.get(x.priority, 9), order[id(x)]))
    return pool[0] if pool else None


def add(tasks, title, role, priority="Normal", needs=(), by="manager", roles=None):
    if role not in (roles or ROLES) or priority not in PRIORITIES or by not in WHO:
        raise ValueError(f"invalid role, priority or author: {role}/{priority}/{by}")
    for n in needs:
        _find(tasks, n)
    number = max([int(x.id[1:]) for x in tasks if x.id[1:].isdigit()] + [0]) + 1
    task = Task(f"T{number}", title, role, priority, list(needs), "todo", by, "")
    tasks.append(task)
    if priority == "Urgent":
        _pause_others(tasks, task.id)
    return task


def start(tasks, task_id):
    task = _find(tasks, task_id)
    if task.status not in ("todo", "paused"):
        raise ValueError(f"{task_id} is {task.status}, it cannot be started")
    if not _deps_done(tasks, task):
        raise ValueError(f"{task_id} waits for tasks that are not done yet: {', '.join(task.needs)}")
    if task.priority == "Urgent":
        _pause_others(tasks, task.id)
    elif _open_urgent(tasks):
        raise ValueError("an Urgent task is open: everything else waits")
    if any(x.role == task.role and x.status == "doing" for x in tasks):
        raise ValueError(f"{task.role} already has a task in progress")
    task.status, task.note = "doing", ""
    return task


def finish(tasks, task_id, evidence, reviewed=None):
    if not str(evidence).strip():
        raise ValueError("finishing needs evidence that it was tested")
    task = _find(tasks, task_id)
    if task.role in (reviewed or REVIEWED):
        raise ValueError(f"{task.role} work needs a supervisor: submit it, then approve")
    task.status, task.note = "done", str(evidence).strip()
    _resume_if_clear(tasks)
    return task


def submit(tasks, task_id):
    task = _find(tasks, task_id)
    if task.status != "doing":
        raise ValueError(f"{task_id} is {task.status}: only a task in progress can be submitted")
    task.status, task.note = "review", ""
    return task


def approve(tasks, task_id, evidence):
    if not str(evidence).strip():
        raise ValueError("approving needs evidence that the supervisor ran the tests")
    task = _find(tasks, task_id)
    if task.status != "review":
        raise ValueError(f"{task_id} is {task.status}: only work waiting for review can be approved")
    task.status, task.note = "done", str(evidence).strip()
    _resume_if_clear(tasks)
    return task


def reject(tasks, task_id, reason):
    task = _find(tasks, task_id)
    if task.status != "review":
        raise ValueError(f"{task_id} is {task.status}: only work waiting for review can be rejected")
    task.tries += 1
    if task.tries >= 3:
        task.status = "blocked"
        task.note = f"owner decision needed: rejected {task.tries} times, last reason: {reason}"
    else:
        task.status = "todo"
        task.note = f"rejected ({task.tries}): {reason}"
        if task.priority in ("Normal", "Low"):
            task.priority = "High"
    return task


def set_priority(tasks, task_id, priority, by):
    if priority not in PRIORITIES or by not in WHO:
        raise ValueError(f"invalid priority or author: {priority}/{by}")
    task = _find(tasks, task_id)
    task.priority, task.by = priority, by
    if priority == "Urgent" and task.status != "done":
        _pause_others(tasks, task.id)
    else:
        _resume_if_clear(tasks)
    return task


def placar(tasks) -> dict:
    total = len(tasks)
    done = sum(1 for x in tasks if x.status == "done")
    building = [{"id": x.id, "title": x.title, "status": x.status, "note": x.note}
                for x in tasks if x.status in ("doing", "review", "paused", "blocked")]
    return {"total": total, "done": done, "percent": done * 100 // total if total else 0,
            "in_construction": building, "waiting": sum(1 for x in tasks if x.status == "todo")}


def validate(tasks, roles=None) -> list:
    problems, seen = [], set()
    for x in tasks:
        if x.id in seen:
            problems.append(f"{x.id}: duplicate id")
        seen.add(x.id)
        if x.role not in (roles or ROLES):
            problems.append(f"{x.id}: unknown role {x.role}")
        if x.priority not in PRIORITIES:
            problems.append(f"{x.id}: unknown priority {x.priority}")
        if x.status not in STATUSES:
            problems.append(f"{x.id}: unknown status {x.status}")
        if x.status in ("blocked", "paused") and not x.note.strip():
            problems.append(f"{x.id}: {x.status} without a reason (note)")
        if x.status == "done" and not x.note.strip():
            problems.append(f"{x.id}: done without evidence (note)")
        for n in x.needs:
            if n not in {y.id for y in tasks}:
                problems.append(f"{x.id}: depends on unknown task {n}")
    for role in sorted({x.role for x in tasks}):
        if sum(1 for x in tasks if x.role == role and x.status == "doing") > 1:
            problems.append(f"role {role} has two tasks in progress")
    by_id = {x.id: x for x in tasks}
    visiting, finished = set(), set()

    def walk(task_id):
        if task_id in finished or task_id not in by_id:
            return False
        if task_id in visiting:
            return True
        visiting.add(task_id)
        loop = any(walk(n) for n in by_id[task_id].needs)
        visiting.discard(task_id)
        finished.add(task_id)
        return loop
    if any(walk(x.id) for x in tasks):
        problems.append("cycle in dependencies")
    return problems


def release_problems(tasks, owner_ok, reviewed=None) -> list:
    problems = [f"{x.id} ({x.role}) is {x.status}: {x.title}" for x in tasks if x.role in (reviewed or REVIEWED) and x.status != "done"]
    for role in ("QA", "Security"):
        if not any(x.role == role and x.status == "done" for x in tasks):
            problems.append(f"no {role} task is done and approved")
    if not owner_ok:
        problems.append("the owner's final test is not recorded (the owner must say yes, then: release-ok)")
    return problems


RELEASE_PATTERNS = [r"\bgit\s+commit\b", r"\bgit\s+push\b", r"\bgit\s+tag\b", r"\bnpm\s+publish\b", r"\bgh\s+release\b",
                    r"\btwine\s+upload\b", r"\bdocker\s+push\b", r"\bcargo\s+publish\b",
                    r"\bwrangler\s+(deploy|publish)\b", r"\bgh\s+pr\s+merge\b"]


def is_release_command(command) -> bool:
    return any(re.search(pattern, command or "") for pattern in RELEASE_PATTERNS)


def owner_ok(project) -> bool:
    try:
        return bool(json.loads((Path(project) / ".crewcraft" / "liberacao.json").read_text(encoding="utf-8")).get("owner_ok"))
    except (OSError, ValueError):
        return False


SIGN_ROLES = ["qa", "security", "test", "manager"]


def sign(project, who, evidence, by="unknown") -> dict:
    if who not in SIGN_ROLES:
        raise ValueError(f"who must be one of: {', '.join(SIGN_ROLES)}")
    if not str(evidence).strip():
        raise ValueError("a signature needs evidence: what was checked and the real result")
    path = Path(project) / ".crewcraft" / "assinaturas.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    data[who] = {"evidence": str(evidence).strip(), "by": by, "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data[who]


def signoff_problems(project) -> list:
    path = Path(project) / ".crewcraft" / "assinaturas.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return [f"missing signature: {who} (the delivery is signed by QA, Security, the test supervisor and the manager)"
            for who in SIGN_ROLES if not str(data.get(who, {}).get("evidence", "")).strip()]


def _queue_path(project: Path) -> Path:
    return project / ".crewcraft" / "fila.md"


def load(project_dir) -> list:
    return parse(_queue_path(Path(project_dir)).read_text(encoding="utf-8"))


def save(project_dir, tasks):
    path = _queue_path(Path(project_dir))
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    tail = "".join(l + "\n" for l in old.replace("\r\n", "\n").split("\n") if l and not l.startswith("|") and not l.startswith("#")
                   and l not in HEADER)
    path.write_text(serialize(tasks) + tail, encoding="utf-8")


def log_event(project_dir, task, event, **extra):
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "role": task.role, "task": task.id, "event": event, **extra}
    with open(Path(project_dir) / ".crewcraft" / "eventos.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _option(args, name, default=None):
    if name in args:
        i = args.index(name)
        value = args[i + 1] if i + 1 < len(args) else default
        del args[i:i + 2]
        return value
    return default


def main(argv) -> int:
    args = list(argv[1:])
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(args[0]))
        command, rest = args[1], args[2:]
        if command == "init":
            (project / ".crewcraft").mkdir(exist_ok=True)
            template = Path(__file__).resolve().parents[1] / "templates" / "fila.md"
            created = _copy_if_missing(template, _queue_path(project))
            print("created fila.md" if created else "fila.md already exists")
            return 0
        tasks = load(project)
        try:
            from scripts.cargos import reviewed_roles, role_names
        except ImportError:
            from cargos import reviewed_roles, role_names
        roles, reviewed = role_names(project), reviewed_roles(project)
        if command == "add":
            priority, needs, by = _option(rest, "--priority", "Normal"), _option(rest, "--needs", ""), _option(rest, "--by", "manager")
            task = add(tasks, rest[0], rest[1], priority, [n for n in needs.split(",") if n], by, roles)
            log_event(project, task, "add", priority=priority, by=by)
            print(f"{task.id} added")
        elif command == "next":
            task = next_task(tasks, rest[0])
            print(f"{task.id}: {task.title} ({task.priority})" if task else f"nothing for {rest[0]} right now")
        elif command == "start":
            task = start(tasks, rest[0])
            log_event(project, task, "start")
            print(f"{task.id} started")
        elif command == "finish":
            task = finish(tasks, rest[0], rest[1] if len(rest) > 1 else "", reviewed)
            log_event(project, task, "finish", evidence=task.note)
            print(f"{task.id} done and tested")
        elif command == "submit":
            task = submit(tasks, rest[0])
            log_event(project, task, "submit")
            print(f"{task.id} waits for the supervisor")
        elif command == "approve":
            by = _option(rest, "--by", "supervisor")
            task = approve(tasks, rest[0], rest[1] if len(rest) > 1 else "")
            log_event(project, task, "approve", by=by, evidence=task.note)
            print(f"{task.id} approved: done and tested")
        elif command == "reject":
            by = _option(rest, "--by", "supervisor")
            task = reject(tasks, rest[0], rest[1] if len(rest) > 1 else "no reason given")
            log_event(project, task, "reject", by=by, reason=task.note)
            print(f"{task.id} sent back ({task.status}, try {task.tries})")
        elif command == "sign":
            by = _option(rest, "--by", "unknown")
            signed = sign(project, rest[0], rest[1] if len(rest) > 1 else "", by)
            print(f"{rest[0]} signed ({signed['time']})")
        elif command == "release-check":
            try:
                from scripts.robustez import problems as robust_problems
            except ImportError:
                from robustez import problems as robust_problems
            problems = release_problems(tasks, owner_ok(project), reviewed) + robust_problems(project) + signoff_problems(project)
            print("\n".join(problems) if problems else "OK: release allowed")
            return 1 if problems else 0
        elif command == "release-ok":
            (project / ".crewcraft" / "liberacao.json").write_text(json.dumps(
                {"owner_ok": True, "note": rest[0] if rest else "", "time": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                ensure_ascii=False), encoding="utf-8")
            print("owner's final test recorded")
        elif command == "priority":
            by = _option(rest, "--by", "manager")
            task = set_priority(tasks, rest[0], rest[1], by)
            log_event(project, task, "priority", priority=rest[1], by=by)
            print(f"{task.id} is now {rest[1]} (set by {by})")
        elif command == "placar":
            score = placar(tasks)
            print(f"{score['done']} of {score['total']} done and tested ({score['percent']}%), "
                  f"{len(score['in_construction'])} in construction, {score['waiting']} waiting")
            for item in score["in_construction"]:
                print(f"  {item['id']} {item['status']}: {item['title']} {item['note']}".rstrip())
            return 0
        elif command == "validate":
            problems = validate(tasks, roles)
            print("\n".join(problems) if problems else "OK")
            return 1 if problems else 0
        else:
            print(f"unknown command: {command}")
            return 2
        save(project, tasks)
        return 0
    except (ValueError, FileNotFoundError, IndexError) as error:
        print(error if not isinstance(error, IndexError) else "missing argument")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
