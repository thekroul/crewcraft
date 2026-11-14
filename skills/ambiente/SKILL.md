---
name: ambiente
description: Use when a project starts on a computer the crew has not seen, when a test or build tool is missing, or when the owner asks what this computer can do. Finds what is installed and suggests, for each job, the best option with its weakness explained.
---

# Ambiente (what this computer can do)

Nothing about tools is fixed in advance. For each person and each computer, find what is already installed and suggest the rest by job (testing in a clean environment, checking in a browser, version control), instead of assuming a particular tool.

The plugin root is two folders above this skill's folder (`../../`). Detect with:

`python <plugin root>/scripts/ambiente.py`

It installs nothing and sends nothing anywhere. It prints, for each job, the options in order (what is ready first), with each option's weakness in plain words and how to get it.

## What to do with the result

1. Tell the person in plain words what is ready and what the best ready option cannot catch. Example: a second Windows user is ready, but it shares the same system files, so it will not catch a problem caused by a component that only this PC has.
2. If a better option is missing, say how to get it and what it would change. Do not install or download anything without approval: when asking, say the filename, the source and the size.
3. Keep the sheet in the person's own Claude configuration folder (`crewcraft/ambiente.md`, next to the level profile), never in the plugin and never in a project folder: it describes the computer, not the project. Run `python <plugin root>/scripts/ambiente.py --out <that file>`. Read it again at the start of work and refresh it when something was installed or the person asks.
4. Use the sheet when dispatching QA and Security: tell them which clean environment is available, so they can say which problems it cannot catch.

## Warning signs

- Naming one tool as the answer for everyone.
- Installing something before asking.
- Writing the sheet into the plugin or into a project.
- Hiding the weakness of the option that is available.
