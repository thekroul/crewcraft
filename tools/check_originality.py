"""Originality checker: no text copied from third-party skills.

Usage: python tools/check_originality.py <plugin_root> <corpus_dir> [--limit N]
Flags a plugin file sharing N or more 8-word sequences with any .md file of the corpus.
"""
import re
import sys
from pathlib import Path

SUFFIXES = {".md"}
SKIP_DIRS = {".git", "tests", "tools", "__pycache__"}


def shingles(text: str, n: int = 8) -> set[tuple[str, ...]]:
    words = re.findall(r"[^\W_]+", text.lower())
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _corpus_index(corpus: Path, n: int) -> dict[tuple[str, ...], str]:
    index: dict[tuple[str, ...], str] = {}
    for path in corpus.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for shingle in shingles(text, n):
            index.setdefault(shingle, path.name)
    return index


def check_originality(root: Path, corpus: Path, n: int = 8, limit: int = 3) -> list[str]:
    index = _corpus_index(corpus, n)
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        shared = [index[s] for s in shingles(path.read_text(encoding="utf-8", errors="replace"), n) if s in index]
        if len(shared) >= limit:
            source = max(set(shared), key=shared.count)
            errors.append(f"{relative.as_posix()}: {len(shared)} shared {n}-word sequences with {source}")
    return errors


def main(argv: list[str]) -> int:
    args = argv[1:]
    limit = 3
    if "--limit" in args:
        index = args.index("--limit")
        limit = int(args[index + 1])
        del args[index:index + 2]
    root, corpus = Path(args[0]), Path(args[1])
    errors = check_originality(root, corpus, limit=limit)
    for error in errors:
        print(error)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
