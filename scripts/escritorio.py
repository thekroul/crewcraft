"""Optional pixel office: shows the crew working, read from the project's own files.

Usage: python scripts/escritorio.py <absolute project folder> [--port 8765] [--print-state]
Serves one page on 127.0.0.1 only (nothing leaves the computer). It only READS
.crewcraft/fila.md and .crewcraft/eventos.jsonl and never commands anyone.
Off by default: it runs only when someone starts it.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from scripts.cargos import role_names
    from scripts.fila import load, placar
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from cargos import role_names
    from fila import load, placar
    from init_ficha import _checked_project

NAMES = {"Dev": "Ana", "Design": "Bruno", "QA": "Carla", "Security": "Davi", "Support": "Eva", "Marketing": "Félix"}
POOL = ["Gabi", "Hugo", "Iris", "Joao", "Lia", "Marco", "Nina", "Otto", "Paula", "Rui", "Sara", "Tomas", "Vera", "Yuri", "Zeca"]


def _names(roles) -> dict:
    names, extra = {}, 0
    for role in roles:
        if role in NAMES:
            names[role] = NAMES[role]
        else:
            names[role] = POOL[extra % len(POOL)] + (str(extra // len(POOL) + 1) if extra >= len(POOL) else "")
            extra += 1
    return names
PAGE = Path(__file__).resolve().parents[1] / "templates" / "escritorio" / "index.html"


def build_state(project) -> dict:
    project = Path(project)
    queue = project / ".crewcraft" / "fila.md"
    tasks = load(project) if queue.is_file() else []
    roles = []
    every = role_names(project)
    names = _names(every)
    for role in every:
        mine = [x for x in tasks if x.role == role]
        if not mine:
            continue
        pick = {s: next((x for x in mine if x.status == s), None) for s in ("doing", "review", "blocked", "paused")}
        if pick["doing"]:
            state, task = "work", pick["doing"].title
        elif pick["review"]:
            state, task = "review", pick["review"].title
        elif pick["blocked"] or pick["paused"]:
            state, task = "blocked", (pick["blocked"] or pick["paused"]).title
        else:
            state, task = "idle", ""
        roles.append({"role": role, "name": names[role], "state": state, "task": task})
    events = []
    log = project / ".crewcraft" / "eventos.jsonl"
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines()[-8:]:
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    return {"roles": roles, "placar": placar(tasks) if tasks else None, "events": events}


def make_server(project, port=8765):
    project = Path(project)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = self.path.split("?")[0]
            if route in ("/", "/index.html"):
                body, kind = PAGE.read_bytes(), "text/html; charset=utf-8"
            elif route == "/state.json":
                body, kind = json.dumps(build_state(project), ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv) -> int:
    args = list(argv[1:])
    port = 8765
    if "--port" in args:
        i = args.index("--port")
        port = int(args[i + 1])
        del args[i:i + 2]
    print_state = "--print-state" in args
    if print_state:
        args.remove("--print-state")
    if not args:
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(args[0]))
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    if print_state:
        print(json.dumps(build_state(project), ensure_ascii=False, indent=2))
        return 0
    server = make_server(project, port)
    print(f"Office open at http://127.0.0.1:{server.server_address[1]} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
