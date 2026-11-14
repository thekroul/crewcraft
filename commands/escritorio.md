---
description: Open the optional pixel office that shows the crew working (read-only, local, off unless you start it).
argument-hint: "[port, default 8765]"
---

Start the optional office for the current project.

1. Confirm which folder is the project (use the working directory when it is clearly one project; ask when it holds several). The project needs a `.crewcraft/fila.md`; if it has none, say so and stop.
2. Find the plugin root: the folder that contains `.claude-plugin/plugin.json` named `crewcraft`.
3. Run in the background: `python <plugin root>/scripts/escritorio.py <absolute project folder> --port <port from $ARGUMENTS, else 8765>`.
4. Tell the person to open `http://127.0.0.1:<port>` in their browser. The page only reads the project's queue and event log, listens on this computer only, and shows each role at a desk: working roles show the task above their head, idle roles walk around, drink water and chat.
5. Stop the process when the person asks.
