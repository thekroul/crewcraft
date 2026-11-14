"""Mask client data in a log before anyone analyses it.

Usage: python scripts/mask.py <log file> [--out <masked file>]
Masks CPF, CNPJ, invoice keys, e-mails, IPv4 addresses, secrets (password, token, key)
and Windows user folder names. Useful diagnostic text (error codes, versions, times) is kept.
The original file is never changed. Without --out the masked text is printed.
"""
import re
import sys
from pathlib import Path

RULES = [
    ("NFE-KEY", re.compile(r"\b\d{44}\b"), "[NFE-KEY]"),
    ("CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{14}\b"), "[CNPJ]"),
    ("CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b"), "[CPF]"),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
    ("SECRET", re.compile(r"(?i)\b(senha|password|pwd|passwd|token|secret|api[_-]?key)(\s*[:=]\s*)([^\s;,\"']+)"),
     r"\1\2[SECRET]"),
    ("USER", re.compile(r"(?i)([A-Z]:\\Users\\)[^\\\s]+"), r"\1[USER]"),
]


def mask_with_counts(text: str):
    counts = {}
    for name, pattern, replacement in RULES:
        text, found = pattern.subn(replacement, text)
        if found:
            counts[name] = found
    return text, counts


def mask(text: str) -> str:
    return mask_with_counts(text)[0]


def main(argv) -> int:
    args = list(argv[1:])
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = Path(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    masked, counts = mask_with_counts(Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    if out:
        out.write_text(masked, encoding="utf-8")
        print("masked:", ", ".join(f"{k} x{v}" for k, v in counts.items()) or "nothing to mask")
    else:
        sys.stdout.write(masked)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
