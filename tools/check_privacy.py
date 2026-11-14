"""Privacy checker: nothing personal may ship inside the public plugin.

Usage: python tools/check_privacy.py <plugin_root> [--private-list <file>]
The private list (one term per line, '#' comments) lives OUTSIDE the plugin.
Skips the `tools` and `tests` folders because they define the patterns.
"""
import re
import sys
from pathlib import Path

BUILTIN = [
    ("windows user path", re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE)),
    ("unix user path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")),
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("secret assignment", re.compile(r"(?:api[_-]?key|secret|password)\W{0,3}\s*[:=]\s*\S+", re.IGNORECASE)),
]
SUFFIXES = {".md", ".json", ".py", ".html", ".css", ".txt", ".yml", ".yaml"}
SKIP_ALL = {".git", "__pycache__", "results"}
SKIP_BUILTIN = {"tools", "tests"}  # they define the patterns; private terms are still checked there


def check_privacy(root: Path, extra_patterns: list[str]) -> list[str]:
    errors: list[str] = []
    terms = [
        (t.strip().lower(), re.compile(rf"(?<!\w){re.escape(t.strip())}(?!\w)", re.IGNORECASE))
        for t in extra_patterns if t.strip()
    ]
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        if any(part in SKIP_ALL for part in relative.parts):
            continue
        check_builtin = not any(part in SKIP_BUILTIN for part in relative.parts)
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in (BUILTIN if check_builtin else []):
                if pattern.search(line):
                    errors.append(f"{relative.as_posix()}:{number}: {label}")
            for term, pattern in terms:
                if pattern.search(line):
                    errors.append(f"{relative.as_posix()}:{number}: private term '{term}'")
    return errors


def main(argv: list[str]) -> int:
    args = argv[1:]
    private: list[str] = []
    if "--private-list" in args:
        index = args.index("--private-list")
        lines = Path(args[index + 1]).read_text(encoding="utf-8").splitlines()
        private = [l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")]
        del args[index:index + 2]
    root = Path(args[0]) if args else Path(".")
    errors = check_privacy(root, private)
    for error in errors:
        print(error)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
