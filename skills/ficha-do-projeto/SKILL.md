---
name: ficha-do-projeto
description: Use when a project needs its decision log, question list or visual profile created or updated, or when a conversation about a project starts and a `.crewcraft` folder does not exist yet. Keeps everything about one project inside that project's own folder.
---

# Ficha do projeto (the project's own folder)

Everything the crew learns about a project lives in a `.crewcraft` folder **inside that project**. Nothing about a project is stored in the plugin, and nothing is shared between projects.

## What is in the folder

| File | Holds |
|---|---|
| `decisoes.md` | Every settled choice: id, decision, who made it (`owner` or `suggestion`), date |
| `perguntas.md` | Questions still open and the answers once given |
| `ficha-visual.md` | Palette, typography, density, shape, qualities taken from approved references, and the banned "AI look" list |
| `prototipos/` | Mockups shown to the owner (created by the `prototipo-visual` skill) |

The user's own level profile is **not** here. It stays in the user's Claude configuration folder (see `conversa`).

## Creating it

First confirm which folder is the project. If the session's working directory is clearly one project, or a new empty folder, use it and say its full path in one line. If it holds several separate projects or looks like a general folder (home, Documents), ask which one is the project and write only after the answer. Never create `.crewcraft` in a folder that holds several projects, because the folder would end up shared between them.

The plugin root is two folders above this skill's folder (`../../`). Run the helper with the absolute path of the script and the absolute path of the project folder:

`python <plugin root>/scripts/init_ficha.py <absolute project folder>`

It creates only the files that are missing and never overwrites one the owner has edited. If Python is not available, copy the three files from `templates/` by hand and apply the same rule: never overwrite.

It refuses any path inside a folder the owner listed as read-only, even through `.` or `..`. That folder is read-only by the owner's rule: do not work around the refusal, and do not copy the files by hand into it either. Tell the owner and keep the files somewhere they approve. The owner controls that list (`somente-leitura.txt`, in the `crewcraft` folder of the Claude configuration folder): if the owner explicitly allows writing in a listed folder, confirm it, remove the entry and proceed.

## Client variants (variantes)

When the same product is customised for different clients, keep one `ficha-visual.md` for the project and, for each client, a small file `.crewcraft/variantes/<client>/ficha-visual.md` that lists **only what differs**. Anything left empty is inherited from the project, so an improvement to the project reaches every client without rework. Create one with:

`python <plugin root>/scripts/init_ficha.py <absolute project folder> --variant <client name>`

Never copy one client's decisions or notes into another client's variant.

## Keeping it up to date

- A decision is added the moment it is settled, not at the end of the session.
- `owner` means the person said it. `suggestion` means you proposed it and they accepted. Never write a proposal they have not accepted.
- When a decision changes, add a new row that replaces the old one and mention the old id. Do not rewrite history.
- A reference the owner pastes becomes a line in `Reference qualities` (what makes it good), never a copy of the design.
- When the owner says something looks like AI made it, add what they disliked to `Banned (AI look)`.

## Warning signs

- Project facts written into the plugin folder.
- A file overwritten without the owner knowing.
- Decisions recorded at the end from memory instead of as they happened.
