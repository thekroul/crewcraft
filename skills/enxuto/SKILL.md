---
name: enxuto
description: Use when about to add a dependency, library, file, abstraction, setting or feature the owner did not ask for, or when the owner asks whether a project carries more than it needs. Does the minimum that fully meets the request, at full quality, and reports what was left out.
---

# Enxuto (lean: the least that fully does the job)

Build the smallest thing that completely meets the request. Lean never costs safety or finish: it means nothing that nobody asked for.

The plugin root is two folders above this skill's folder (`../../`).

## Before adding anything

1. Was it asked for, or required by a decision in `.crewcraft/decisoes.md`? If not, do not add it.
2. Does the language's standard library (stdlib) already do it? Use that first.
3. Does the project already have something that does it?
4. Would a few lines replace the dependency? Prefer the few lines.
5. If it still earns its place, count what it costs: size, upkeep, security surface, license.

## What is never cut

Input validation, security, accessibility, error messages a support person can use, and tests. Lean removes extras, not safeguards.

## Audit what is already there

Run `python <plugin root>/scripts/enxuto.py <absolute project folder>`. It lists dependencies that are declared but never imported. Remove one only with a reason, and ask before removing something the owner might still use.

## Say what was left out

Every delivery ends with a short line in plain words about what was left out and why, so the owner can overrule it. Example: for a calculator, "no history, no cloud sync and no extra libraries: you asked for the four operations, and the standard library covers them".

## Warning signs

- A library added for something the standard library does.
- A layer, setting or option nobody asked for.
- A dependency left in after the code stopped using it.
- Cutting a safeguard in the name of lean.
