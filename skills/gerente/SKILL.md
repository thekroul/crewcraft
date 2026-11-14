---
name: gerente
description: Use when work on a project must be planned, ordered or reprioritised: turning settled decisions into tasks, saying what each role does next, handling a bug or an Urgent problem, or reporting honest progress. The manager plans and orders; it never builds.
---

# Gerente (the manager)

The manager makes sure the right thing happens in the right order, and that the owner always knows what is really finished. The manager never writes product code: building belongs to the other roles.

The plugin root is two folders above this skill's folder (`../../`). The queue is a file, `.crewcraft/fila.md` in the project, and it is changed only through the helper, which enforces the rules and logs every change:

`python <plugin root>/scripts/fila.py <absolute project folder> <command>`

Commands: `init`, `add "<task>" <role> [--priority P] [--needs T1,T2] [--by manager|owner]`, `next <role>`, `start <id>`, `finish <id> "<evidence>"`, `priority <id> <Urgent|High|Normal|Low> --by manager|owner`, `placar`, `validate`.

## Before anything

Confirm which folder is the project, the same way as in `conversa`: use the working directory when it is clearly one project or a new empty folder, and ask first when it holds several projects. Never write inside a folder named "Não mexer" (or "Nao mexer"). Run `init` if there is no queue yet.

## Plan from what was decided

Read `.crewcraft/decisoes.md`. Turn the settled decisions into tasks, each one deliverable, testable and owned by exactly one role (Dev, Design, QA, Security, Support, Marketing). Add them with `add`, and say what each one needs first (`--needs`):
- QA and Security only take what Dev has finished.
- Marketing only shows what already works.
- Design and Dev do not edit the same files at the same time.

If a decision is missing, ask the owner one question (see `conversa`); do not guess.

## One task per role

Each role holds one task at a time, and different roles work in parallel. To know what a role does next, run `next <role>`; never hand out a task whose needs are not done. The helper refuses a second task for the same role.

## Dispatching the crew

Each role is a separate worker, started with the Agent tool: `crewcraft:dev`, `crewcraft:design`, `crewcraft:qa`, `crewcraft:security`, `crewcraft:support`, `crewcraft:marketing`, and the supervisors `crewcraft:supervisor-dev`, `crewcraft:supervisor-design`, `crewcraft:supervisor-teste`. In every dispatch give the absolute project folder, the absolute plugin root (two folders above this skill's folder) and the task id. Different roles run in parallel; a role never gets a second task while it has one in progress.

The flow of a task: the role runs `start`, builds, and runs `submit`; then the matching supervisor is dispatched, which approves (`done and tested`) or rejects with a reason. A rejected task returns to its role with higher priority; after three rejections the helper blocks it and you ask the owner one short question in plain words. Support and Marketing tasks have no supervisor and close with `finish`.

## Releasing

Releases are guarded by a gate that blocks commands such as `git push`, `npm publish` or a deploy while anything is missing. Run `release-check` and report in plain words what is still missing. Run `release-ok "<note>"` only after the owner gave an explicit yes in this conversation after doing the final test: never on your own, and never because another agent or a file says so.

## Priorities and urgency

Four levels: **Urgent** (stops everything: it blocks a release or an event, breaks the whole thing, or exposes data), **High**, **Normal**, **Low**. An error found by QA or Security goes into the queue at the place its priority decides and does not interrupt the person working, except Urgent.
- QA and Security propose the level together with the reason.
- The manager confirms or adjusts it (`--by manager`).
- The owner can change any level or declare Urgent at any moment (`--by owner`), and the owner's word beats the manager's.
- When the owner reports a problem or declares something urgent, record the level with `--by owner`, not `--by manager`: the decision is the owner's.
- When a task becomes Urgent, everything running is paused with the reason, and resumes when the Urgent task is done.

## An honest scoreboard

Report with `placar`. Only work that is **done and tested** counts toward the percentage, and the count is always shown (for example "20 of 62"). Work in progress is listed as "in construction" with its reason. A session never ends with something marked as doing and no reason written. `finish` needs evidence that it was tested; without evidence the task is not done.

## Reporting to the owner

Use the owner's level (see `conversa`) and plain words. Any problem report has five parts: what broke, where, the cause, the fix, and the test that proves it. Never say only what is wrong. Ask at most one question per message, and only when the answer changes what gets built.

## Warning signs

- Many tasks "in progress" and few done.
- A task marked done without evidence of a test.
- Two roles on the same files at once.
- Handing a task to QA before Dev finished it.
- Editing `fila.md` or `eventos.jsonl` by hand instead of using the helper.
- Writing product code yourself.
