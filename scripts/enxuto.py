"""Lean audit: which declared dependencies does the code never use?

Usage: python scripts/enxuto.py <absolute project folder>
Reads requirements*.txt, pyproject.toml and package.json, scans Python and JavaScript/TypeScript
sources, and lists dependencies that are declared but never imported. Tooling packages (test
runners, linters, type packages) are not reported because configuration files use them.
It only reports; it never changes anything.
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from init_ficha import _checked_project

SKIP = {"node_modules", ".venv", "venv", ".git", "dist", "build", "__pycache__", ".crewcraft", ".claude", "target"}
PY_ALIAS = {"pillow": "pil", "pyyaml": "yaml", "beautifulsoup4": "bs4", "scikit-learn": "sklearn", "opencv-python": "cv2",
            "python-dateutil": "dateutil", "pyjwt": "jwt", "attrs": "attr", "protobuf": "google"}
PY_TOOLS = {"pytest", "pytest-cov", "flake8", "black", "mypy", "ruff", "isort", "coverage", "tox", "pylint", "pre-commit",
            "wheel", "setuptools", "pip", "build", "twine"}
NODE_TOOLS = ("@types/", "eslint", "prettier", "jest", "vitest", "typescript", "webpack", "vite", "ts-node", "nodemon",
              "babel", "@babel/", "rollup", "esbuild", "tsx", "husky", "lint-staged", "playwright", "@playwright/",
              "cypress", "mocha", "chai")
JS_SUFFIX = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def _files(project: Path):
    for folder, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for name in names:
            yield Path(folder) / name


def _python_declared(project: Path) -> list:
    names = []
    for path in project.glob("requirements*.txt"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if line and not line.startswith(("-", "http")):
                names.append(re.split(r"[=<>!~;\[ @]", line, 1)[0].strip())
    toml = project / "pyproject.toml"
    if toml.is_file():
        match = re.search(r"dependencies\s*=\s*\[(.*?)\]", toml.read_text(encoding="utf-8", errors="replace"), re.DOTALL)
        for item in re.findall(r"[\"']([^\"']+)[\"']", match.group(1) if match else ""):
            names.append(re.split(r"[=<>!~;\[ @]", item, 1)[0].strip())
    return [n for n in dict.fromkeys(names) if n]


def _node_root(spec: str):
    if spec.startswith("."):
        return None
    parts = spec.split("/")
    return "/".join(parts[:2]) if spec.startswith("@") else parts[0]


def audit(project) -> dict:
    project = Path(project)
    py_declared = _python_declared(project)
    package = project / "package.json"
    node_declared = []
    if package.is_file():
        data = json.loads(package.read_text(encoding="utf-8", errors="replace"))
        node_declared = list({**data.get("dependencies", {}), **data.get("devDependencies", {})})
    imports, requires = set(), set()
    for path in _files(project):
        if path.suffix == ".py":
            text = path.read_text(encoding="utf-8", errors="replace")
            imports |= {m.lower() for m in re.findall(r"^\s*(?:from|import)\s+([A-Za-z0-9_]+)", text, re.MULTILINE)}
        elif path.suffix in JS_SUFFIX:
            text = path.read_text(encoding="utf-8", errors="replace")
            for spec in re.findall(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)|from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]", text):
                root = _node_root(next(s for s in spec if s) if any(spec) else "")
                if root:
                    requires.add(root)
    py_unused = [n for n in py_declared if n.lower() not in PY_TOOLS
                 and PY_ALIAS.get(n.lower(), n.lower().replace("-", "_")) not in imports]
    node_unused = [n for n in node_declared if not n.startswith(NODE_TOOLS) and n not in requires]
    return {"python": {"declared": len(py_declared), "unused": py_unused},
            "node": {"declared": len(node_declared), "unused": node_unused}}


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    try:
        result = audit(_checked_project(Path(argv[1])))
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    for kind in ("python", "node"):
        info = result[kind]
        if info["declared"]:
            print(f"{kind}: {info['declared']} declared, {len(info['unused'])} possibly unused")
            for name in info["unused"]:
                print(f"  - {name}: never imported; remove it unless a config file uses it")
    if not result["python"]["declared"] and not result["node"]["declared"]:
        print("no dependency files found: nothing to trim")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
