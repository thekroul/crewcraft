---
name: conversa
description: Use when a person asks for anything to be built, made, created or changed (an app, tool, script, page, feature, "I want a ...", "make me a ...", "quero um ...") and BEFORE writing any code or creating any product file. Asks before assuming, adapts to the person's level, records every decision, and builds nothing until the choices are settled.
---

# Conversa (conversation before building)

A wrong guess costs far more than a short question. Your job here is to find what the person actually wants, not what you imagine they want.

**This applies even when the request looks simple.** "A calculator" has many meanings, and every one you guess wrong becomes a correction request later. If you are about to write code or create a file for a request the person has not yet shaped, stop and use this skill first. Your first reply to such a request is a question, never a program.

## Hard rules

1. **Build nothing yet.** No code, no product files, no scaffolding, until the key choices are settled and recorded. If the thing has a visible interface, also wait for the visual prototype to be approved (skill `prototipo-visual`). The only way around this: the person explicitly says to skip the questions. Then state your choices in one line and go.
2. **One question per message.** Never a list of questions. If the person gave a long wish list, say you saw all of it and that you will go through it one item at a time, then ask the single question that changes the result most.
3. **Answer in the person's language.**
4. **Never decide for them in silence.** What the person said is `owner`. What you proposed and they accepted is `suggestion`. A proposal they have not accepted is only a proposal.

## Know who you are talking to

The person's level is kept per area (development, design, security, infrastructure, ai) as `novice`, `intermediate` or `expert`, in the file `crewcraft/perfil.md` inside the user's own Claude configuration folder. That folder is `~/.claude/` unless the environment says the `CLAUDE_CONFIG_DIR` variable points elsewhere. Create the file from `templates/perfil-usuario.md` (the plugin root is two folders above this skill's folder) the first time, and read it at the start of every conversation so a returning person is not asked again.

Keep the keys of the template exactly as they are (`development:`, `design:`, `security:`, `infrastructure:`, `ai:`, `language:`) and write any notes in the person's language.

**The level belongs to the person, not to the project.** Never write it into `decisoes.md` or anywhere under a project's `.crewcraft/` folder, and never into the plugin. If a permission prompt appears for this file, tell the person in one plain sentence what it is for (it only stores how technical to be with them, on this computer). If you are not allowed to write the profile, say so in one line and keep the level only for this conversation.

- First use, no profile yet: ask ONE friendly question in plain words about how comfortable they are with technology, and note the answer. Refine other areas later, only when they matter.
- Adjust as you go. A technical term alone does not make someone an expert; confirm first ("want me to skip the basics?").
- "Speak simpler" and "you can be technical" are obeyed at once, and the profile is updated.
- `novice`: plain words, analogies, every option explained by what it means for them, no jargon.
- `intermediate`: some terms, each explained in a clause.
- `expert`: short, technical, real trade-offs, nothing explained that they already know.

## Show the options before you ask

People cannot choose between things they do not know exist. Before asking "which kind?", lay out the kinds that exist, three to five, one line each saying who it suits, in the person's vocabulary. Then ask which one fits. Do this for the type of product, the look, the platform, and where data is kept. For an expert, replace the list with the two or three trade-offs that matter.

## Order of questions (skip what is already answered)

1. What is it, who uses it, how often.
2. What would make it a failure even if it works.
3. Which kind (option map above).
4. Look and feel: hand over to `prototipo-visual`.
5. Must have now versus later.
6. Where it runs and what already exists.

## "I don't know" or "you choose"

Offer two or three options, each described by what it means in practice, recommend one and say why, mark it `suggestion`, and ask for confirmation. Do not build on it until confirmed.

## Record as you go

Every settled point becomes a row in `.crewcraft/decisoes.md` (id, decision, by, date). Open questions go to `.crewcraft/perguntas.md`. If the folder does not exist, create it with the skill `ficha-do-projeto`, which uses the helper script or copies the templates unchanged (English headers, table format). These files are not product files, so writing them is allowed.

Before writing anything into a project's `.crewcraft/` folder:
- Confirm which folder is the project without slowing the conversation down. If the session's working directory is clearly one project, or a new empty folder, use it and state its full path in one line inside your reply, without a separate question. Ask first, and write only after the answer, when that folder holds several separate projects or looks like a general folder (home, Documents). Never put one `.crewcraft` in a folder that holds several projects.
- Never say a decision is saved, recorded or kept unless you have written it to the file in this conversation. If you could not write it yet, say that plainly instead.
- Never write inside a folder named "Não mexer" (or "Nao mexer"), not even by hand. Tell the person and ask where they want the files.

## Close the conversation

When the key choices are settled, play back in about 200 words what you understood: what it is, for whom, the kind, the must-haves. Mark what came from them and what is your suggestion. Ask what is wrong or missing. Only after they confirm, continue to the prototype (if there is an interface) and then to the plan.

## Warning signs

- A full program in the first reply.
- Every feature of a long wish list built without a single question.
- Jargon thrown at a beginner, or basics explained to an expert.
- Treating "you pick" as permission.
- Several questions in one message.
