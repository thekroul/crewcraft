"""Should this project use a local search over its documents (RAG)? Advice only.

Usage: python scripts/rag_advice.py <absolute project folder>
Counts the project's documents (.crewcraft/*.md and docs/**/*.md) and recommends a level.
It installs nothing: any download needs the owner's approval first.
"""
import re
import shutil
import sys
from pathlib import Path

try:
    from scripts.init_ficha import _checked_project
except ImportError:  # run as a plain script
    from init_ficha import _checked_project


def advise(project) -> dict:
    project = Path(project)
    files = list((project / ".crewcraft").glob("*.md")) + list((project / "docs").rglob("*.md"))
    words = sum(len(re.findall(r"\w+", f.read_text(encoding="utf-8", errors="replace"))) for f in files)
    level = "recommended" if words >= 8000 or len(files) >= 12 else "worth considering" if words >= 3000 or len(files) >= 6 else "not needed"
    return {"level": level, "words": words, "documents": len(files)}


def render(advice, ollama) -> str:
    why = {"recommended": "The documents (plan, research, decisions) are now larger than what is sensible to load into every conversation. A search that finds only the relevant passages keeps answers accurate and cheaper.",
           "worth considering": "The documents are growing. Simple search still works; a local search over them starts to pay off as the plan and research grow.",
           "not needed": "The documents are small. Load them directly; a search layer would only add weight."}[advice["level"]]
    state = ("Ollama is ready on this computer: it can serve the small model that turns text into searchable form."
             if ollama else "Ollama is not installed: it would serve the small model that turns text into searchable form.")
    return "\n".join([
        "# Documentation search advice", "",
        f"Documents: {advice['documents']}, about {advice['words']} words. Level: {advice['level']}.", why, "",
        "Options:",
        f"- Local search over the documents (RAG): splits the project's documents into passages, finds the closest ones to a question and hands only those to the answer. {state} "
        "Weakness: a wrong passage can be answered with confidence, so every answer must show its source passage; it needs the index refreshed when documents change, and a small model uses memory and time.",
        "- Simple search (grep or ripgrep): exact words only. Weakness: misses synonyms and questions asked in other words. Already available on most computers.", "",
        "Nothing is installed without your approval: the filename, the source and the size come first. The index stays on this computer.", ""])


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    try:
        project = _checked_project(Path(argv[1]))
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    print(render(advise(project), bool(shutil.which("ollama"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
