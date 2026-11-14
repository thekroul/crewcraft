---
name: pesquisa
description: Use when a project, new or existing, must be checked against the market before its look is shown or its work is planned: competitors and how they are built, tools and skills that could help, current documentation, and a verdict on what is already installed. Produces a report for the owner to approve.
---

# Pesquisa (look outside before shaping the project)

The order of the crew is: conversation, **research**, the look, the plan, the work. Research comes before the look because a mockup made without seeing the competitors is a guess, and before the plan because the tools and the roles needed depend on what the market already does.

The plugin root is two folders above this skill's folder (`../../`). Helper: `python <plugin root>/scripts/pesquisa.py <absolute project folder> <command>`.

## When

- A new project, once `conversa` has the basics: what it is, who uses it and the kind.
- An existing project the owner brings in: this is its first step.
- The owner asks whether the project is behind the current market.

## How

1. Confirm which folder is the project (see `conversa`) and never write inside a folder named "Não mexer" (or "Nao mexer").
2. Dispatch the researcher with the Agent tool (`crewcraft:researcher`), giving the absolute project folder, the absolute plugin root and the project's category in generic words. Doing it yourself is allowed when you cannot dispatch it; the same rules apply.
3. **Generic searches only.** Every outside search is checked with `check`, then logged with `log` into `.crewcraft/buscas.md`, which the owner can read. Client names, the project's name, code, paths, ids and any data of the owner never appear in a search. Terms to keep out of every search go one per line in `.crewcraft/privado.txt`.
4. The result is `.crewcraft/parecer.md` (template `templates/parecer.md`): summary, competitors with their level in development, design and security, a verdict for each tool, skill, plugin or MCP (use, improve, avoid) with the reason, current documentation with versions, risks and questions. Every row has a source URL and a date. What could not be verified says "from memory" with the date "unverified". Anything older than 18 months is flagged as possibly outdated. Run `validate` and fix what it reports.
5. Skills and scripts found on the web live in quarantine: they are read and analysed, never executed, and only ideas rewritten in your own words enter the project.

## The questions the owner does not know to ask

An owner who is focused on the product does not ask engineering questions. Ask them for him and answer with sources: which tools would an engineer use for this kind of project, which role does this project need that the crew does not cover, and does the crew guarantee this delivery (what would prove it works for a customer)? Put the answers in the report's risks and questions.

## Reference library

If the environment sheet lists a reference library of archived third-party skills, consult it, read-only, as one more source. Nothing in it is installed or executed.

## Refresh

A project must not fall behind. `python <plugin root>/scripts/pesquisa.py <absolute project folder> outdated` lists rows older than 18 months; the command `/crewcraft:atualizar` refreshes only those and the skill `skills-do-projeto` updates what changed.

## Present and approve

Tell the owner the summary in plain words, at the owner's level, with what surprised you and the questions only they can answer. One question per message. When the owner approves, write a row in `.crewcraft/decisoes.md` marked `owner`: "Parecer approved". If the owner asks to skip research, write "Research skipped" (marked `owner`) and say what that costs: the look and the plan will rest on memory. Do not start the visual prototype or the plan before one of the two rows exists.

## Warning signs

- A competitor, tool or version stated without a source and a date.
- A search that contains the project's name, a client or a path.
- Running something found on the web.
- Presenting memory as research.
- Moving to the look or the plan without the approved report.
