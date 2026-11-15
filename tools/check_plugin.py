"""Structure checker for the Crewcraft plugin package.

Usage: python tools/check_plugin.py <plugin_root>
Exit code 1 if any rule is broken.
"""
import json
import re
import sys
from pathlib import Path

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter(path: Path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FRONTMATTER.match(text)
    if not match:
        return None
    fields = {}
    for line in match.group(1).split("\n"):
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def _yaml_problem(path: Path):
    """The header must be real YAML: a plain description containing a colon and a space is silently dropped by Claude Code."""
    match = FRONTMATTER.match(path.read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10)))
    if not match:
        return None
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml:
        try:
            yaml.safe_load(match.group(1))
        except Exception as exc:
            return f"YAML cannot parse the header ({str(exc).splitlines()[0]})"
        return None
    for line in match.group(1).split(chr(10)):
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value and value[0] not in (chr(34), chr(39)) and (": " in value or " #" in value):
                return "YAML cannot parse a plain description containing a colon and a space or a hash: quote it or rephrase"
    return None


def check_plugin(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return [f"{manifest}: plugin.json is missing"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{manifest}: invalid JSON ({exc})"]

    if data.get("name") != "crewcraft":
        errors.append("plugin.json: name must be 'crewcraft'")
    if not SEMVER.match(str(data.get("version", ""))):
        errors.append("plugin.json: version must look like 1.2.3")
    if not str(data.get("description", "")).strip():
        errors.append("plugin.json: description must not be empty")
    if "author" in data:
        errors.append("plugin.json: author field is not allowed yet (owner decides later)")

    market = root / ".claude-plugin" / "marketplace.json"
    if market.is_file():
        try:
            listing = json.loads(market.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"marketplace.json: invalid JSON ({exc})")
            listing = {}
        if "email" in listing.get("owner", {}):
            errors.append("marketplace.json: owner must not carry an email")
        entries = [p for p in listing.get("plugins", []) if p.get("name") == "crewcraft"]
        if not entries:
            errors.append("marketplace.json: must list the plugin 'crewcraft'")
        for entry in entries:
            if entry.get("source") != "./":
                errors.append("marketplace.json: source of crewcraft must be './' (repo root)")

    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        folder = skill.parent.name
        problem = _yaml_problem(skill)
        if problem:
            errors.append(f"skills/{folder}: {problem}")
        fields = _frontmatter(skill)
        if fields is None:
            errors.append(f"skills/{folder}: SKILL.md has no frontmatter")
            continue
        if fields.get("name") != folder:
            errors.append(f"skills/{folder}: frontmatter name must equal the folder name")
        if not fields.get("description", "").startswith("Use when"):
            errors.append(f"skills/{folder}: description must start with 'Use when'")

    for agent in sorted((root / "agents").glob("*.md")):
        problem = _yaml_problem(agent)
        if problem:
            errors.append(f"agents/{agent.stem}: {problem}")
        fields = _frontmatter(agent)
        if not fields:
            errors.append(f"agents/{agent.stem}: no frontmatter")
            continue
        if fields.get("name") != agent.stem:
            errors.append(f"agents/{agent.stem}: frontmatter name must equal the file name")
        if not fields.get("description"):
            errors.append(f"agents/{agent.stem}: description is required")
        if agent.stem.startswith("supervisor"):
            bad = [t.strip() for t in fields.get("tools", "").split(",") if t.strip() in ("Edit", "Write", "NotebookEdit")]
            if bad:
                errors.append(f"agents/{agent.stem}: supervisors only guarantee, they must not have {', '.join(bad)}")

    hooks = root / "hooks" / "hooks.json"
    if hooks.is_file():
        try:
            commands = [h.get("command", "") for group in json.loads(hooks.read_text(encoding="utf-8")).get("hooks", {}).values()
                        for entry in group for h in entry.get("hooks", [])]
            errors += [f"hooks/hooks.json: command must use CLAUDE_PLUGIN_ROOT: {c}" for c in commands if "CLAUDE_PLUGIN_ROOT" not in c]
        except (ValueError, AttributeError):
            errors.append("hooks/hooks.json: invalid JSON or structure")

    for command in sorted((root / "commands").glob("*.md")):
        problem = _yaml_problem(command)
        if problem:
            errors.append(f"commands/{command.stem}: {problem}")
        fields = _frontmatter(command)
        if not fields or not fields.get("description"):
            errors.append(f"commands/{command.stem}: frontmatter needs a description")
    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    errors = check_plugin(root)
    for error in errors:
        print(error)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
