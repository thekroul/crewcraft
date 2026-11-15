---
name: prototipo-visual
description: Use when the look of an interface (screens, dashboard, site, app window) must be decided, when the owner says they dislike a look or that it looks like AI made it, or when the owner shares a reference image. Shows mockups in two separate rounds, structure and then theme, and blocks building until the owner approves.
---

# Prototipo visual (see it before it is built)

The owner should never receive a finished interface they have not seen. This skill shows options first, in two rounds that can be changed independently, and nothing visible is built until the owner says yes.

The plugin root is two folders above this skill's folder (`../../`). Mockup templates are in `templates/mockup/`. Project files go in the project's `.crewcraft/` folder (create it with the `ficha-do-projeto` skill if missing); mockups go in `.crewcraft/prototipos/`.

Ask one question per message, even here: the same rule as in `conversa` applies. Confirm which folder is the project before writing anything, and never write inside a folder the owner listed as read-only.

## Before showing anything

0. Research comes first. If `.crewcraft/decisoes.md` has no `owner` row "Parecer approved" and no row "Research skipped", say that the look is shown after the research, and run the skill `pesquisa`. Use the competitors' design qualities from the approved report as the starting point of the three structures.

1. If the project has no `.crewcraft/` folder yet, create it first (skill `ficha-do-projeto`). Then read the project's `ficha-visual.md`. Respect the palette, density and the **Banned (AI look)** list. If it is still the empty template, ask what kind of people will use this and what they dislike, one question.
2. Use believable sample data: uneven numbers, long titles, names that look real. Never round placeholders.

## Round 1: structure

Make exactly three layouts that differ in **structure** (where things sit, what is emphasised), not in color. Copy `base.html` three times (`estrutura-a.html`, `estrutura-b.html`, `estrutura-c.html`) and change the markup. Never write a color value: colors come only from `var(--...)` and from the linked theme file.

Show them, then describe each in one plain sentence and ask which one is closest, or what to mix. If the browser pane is available, show screenshots; otherwise give the file paths to open. Expect the owner to ask for adjustments anyway: that is normal, the goal is to get close, not perfect.

## Round 2: theme

Keep the chosen structure file untouched. Change **only** the one `<link ... href="theme-....css">` line to preview a theme, and write at least three really different theme files (not three shades of the same one). Show them side by side. The structure must not change between themes.

When the owner says it looks like AI made it:
- Do not nudge the same palette. Change direction: one restrained accent plus neutrals, flat surfaces, thin borders, plain type, dense and believable data, no gradients, no glow, no frosted glass.
- Ask for a reference they like (a picture or link).
- Add what they disliked to `Banned (AI look)` in `ficha-visual.md`.

## References from the owner

When the owner shares an image or link:
- Look at it and write down its **qualities**: how many colors, how dense, which shapes, how real the data feels. Save them under `Reference qualities` in `ficha-visual.md`.
- Say plainly that you take the qualities and not the design: the mockups stay your own.
- Do not download images from the internet without asking first, and say file name, source and size when you ask. Viewing a page or taking a screenshot to look at is fine.

## The gate

No product code and no real screens until the owner approves a structure and a theme. When they do, write a row in `decisoes.md` marked `owner` (for example "Visual approved: structure B, theme warm") and fill the palette, typography, density and shape sections of `ficha-visual.md` with the chosen values.

## Warning signs

- Showing one option only, or options that differ only in color.
- Colors typed into the structure file.
- Starting the real interface because "the direction is obvious".
- Copying a competitor's layout instead of taking its qualities.
- Round placeholder numbers in the mockups.
