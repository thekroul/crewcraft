"""Create the `.crewcraft` folder inside a project, from the plugin templates.

Usage: python scripts/init_ficha.py <project_dir> [--variant <client name>]
Never overwrites a file that already exists. Refuses any path inside a folder
named "Não mexer" (read-only by the owner's rule).
"""
import sys
import unicodedata
from pathlib import Path

TEMPLATE_FILES = ["decisoes.md", "perguntas.md", "ficha-visual.md"]
READ_ONLY_FOLDERS = {"nao mexer"}


def _plain(part: str) -> str:
    decomposed = unicodedata.normalize("NFD", part)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _checked_project(project_dir: Path) -> Path:
    """Resolve the path first, so '.' and '..' cannot hide a read-only folder."""
    project_dir = Path(project_dir).resolve()
    for part in project_dir.parts:
        if _plain(part) in READ_ONLY_FOLDERS:
            raise ValueError(f"refusing to write inside a read-only folder: {part}")
    if not project_dir.is_dir():
        raise FileNotFoundError(f"project folder does not exist: {project_dir}")
    return project_dir


def _copy_if_missing(source: Path, destination: Path) -> bool:
    try:
        with open(destination, "x", encoding="utf-8") as handle:
            handle.write(source.read_text(encoding="utf-8"))
    except FileExistsError:
        return False
    return True


def init_variant(project_dir: Path, name: str, templates: Path) -> list[Path]:
    """Create `.crewcraft/variantes/<name>/ficha-visual.md` (differences only). Never overwrites."""
    if not name or name in {".", ".."} or any(sep in name for sep in "/\\"):
        raise ValueError(f"variant name must be a plain folder name: {name!r}")
    project_dir = _checked_project(project_dir)
    folder = project_dir / ".crewcraft" / "variantes" / name
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / "ficha-visual.md"
    return [destination] if _copy_if_missing(Path(templates) / "variante.md", destination) else []


def init_ficha(project_dir: Path, templates: Path) -> list[Path]:
    project_dir = _checked_project(project_dir)
    target = project_dir / ".crewcraft"
    target.mkdir(exist_ok=True)
    created: list[Path] = []
    for name in TEMPLATE_FILES:
        destination = target / name
        if _copy_if_missing(Path(templates) / name, destination):
            created.append(destination)
    return created


def main(argv: list[str]) -> int:
    args = argv[1:]
    variant = None
    if "--variant" in args:
        index = args.index("--variant")
        variant = args[index + 1] if index + 1 < len(args) else ""
        del args[index:index + 2]
    if not args:
        print("usage: init_ficha.py <absolute project_dir> [--variant <client name>]")
        return 2
    templates = Path(__file__).resolve().parents[1] / "templates"
    try:
        if variant is None:
            created = init_ficha(Path(args[0]), templates)
        else:
            created = init_variant(Path(args[0]), variant, templates)
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1
    for path in created:
        print(f"created {path}")
    if not created:
        print("nothing to create (all files already exist)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
