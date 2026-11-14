---
description: Refresh a project's research so it does not fall behind the market (old rows are re-checked, project skills are updated).
argument-hint: "[nothing needed]"
---

Refresh the research of the current project.

1. Confirm which folder is the project (the working directory when it is clearly one project; ask when it holds several). It needs an approved `.crewcraft/parecer.md`; if it has none, run the skill `pesquisa` instead.
2. Find the plugin root (the folder holding `.claude-plugin/plugin.json` named `crewcraft`) and run `python <plugin root>/scripts/pesquisa.py <absolute project folder> outdated`.
3. Dispatch `crewcraft:researcher` to re-check only the rows listed and to look for anything new in the project's category, with the same generic-search rules. It updates each source and date and runs `validate`.
4. Tell the owner in plain words what changed and what it means for the project. When the owner approves, record an `owner` row in `.crewcraft/decisoes.md`: "Parecer approved (refreshed <date>)".
5. Run the skill `skills-do-projeto` to refresh the project skills the changes affect.
