---
name: skills-do-projeto
description: Use when the research report of a project is approved and the project needs its own small skills, or when a project skill must be refreshed. Writes a few lean skills inside the project, aligned with its decisions and sourced, instead of keeping general third-party skills installed.
---

# Skills do projeto (a few skills that belong to one project)

General third-party skills stay out of the way. Each project gets only the skills that fit it, written for it, short, and tied to what the owner decided.

The plugin root is two folders above this skill's folder (`../../`). Helper: `python <plugin root>/scripts/skills_projeto.py <absolute project folder> <command>`.

## When

After the owner approved the research report ("Parecer approved") and before the plan. Again whenever the report is refreshed.

## How

1. Read `.crewcraft/parecer.md` (the verdicts: use, improve, avoid), `.crewcraft/decisoes.md` and `.crewcraft/ficha-visual.md`.
2. Choose few skills, only what this project needs (see `enxuto`). For an item marked "improve", write the improved idea for this project in your own words; copy no text from anyone.
3. For each one run `init <name>`, then fill it in. A project skill is rules for this project in at most 120 lines: what to do, what never to do, and where the details live. Point to the project's own files instead of repeating them.
4. Every skill ends with two lines: `Aligned with:` the decision ids it serves (D3, D7) and `Sources:` a URL with a date (YYYY-MM-DD).
5. Run `validate` and fix what it reports. A skeleton with TODO in it is not finished.
6. Run `claude-md` to refresh the managed Crewcraft block in the project's `CLAUDE.md`. Everything outside the markers is left untouched.

The skills live in the project's `.claude/skills/` folder, so Claude loads them only for this project.

## Third-party skills

Consult them as reference (the reference library in the environment sheet, or what the researcher found), never install them wholesale. Anything from the web is read and analysed in quarantine and never executed.

## Warning signs

- Many skills for a small project.
- A skill without decision ids or without a sourced, dated line.
- Text copied from a third-party skill.
- A skill that repeats the project files instead of pointing to them.
