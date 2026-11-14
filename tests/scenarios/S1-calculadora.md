# S1: conversation scenarios (skill `conversa`)

Run with `tests/scenarios/run-scenario.sh <id> <baseline|plugin> "<prompt>" ["<next prompt>"]`.
Baseline = no plugin, user plugins disabled. Plugin = same, plus `--plugin-dir`.
Outputs go to `tests/scenarios/results/` (not published).

A scenario passes only when EVERY expected behavior is present in the plugin run.

## S1a: vague request from a layperson
Prompt: `quero uma calculadora para Linux`
Expected:
1. No code and no product files are created.
2. The reply asks ONE question (calculator type or visual direction), not a list.
3. It first lays out the kinds of calculator that exist (simple, scientific, financial, programmer) in plain words, so the owner can choose without knowing them.
4. Plain Portuguese, no jargon.

## S1b: "I don't know" / "you choose"
Prompts: `quero uma calculadora para Linux` then `não sei, escolhe você`
Expected on the second reply:
1. Offers explained options with a recommendation and the reason.
2. Presents the pick as a suggestion for the owner to confirm, not as a decision already taken.
3. Still creates no product code.

## S1c: huge request at once
Prompt: `quero uma calculadora com histórico, modo científico, conversão de moedas, tema escuro, atalhos de teclado, exportar para PDF, gráfico de funções, memória, voz e sincronização na nuvem`
Expected:
1. At most ONE question in the reply.
2. No code.
3. Acknowledges the list instead of ignoring it, and says it will go through it step by step.

## S1d: expert user
Prompt: `Sou engenheiro de IA. Quero uma calculadora de linha de comando em Rust, avaliando expressões com precedência correta.`
Expected:
1. Short reply, technical vocabulary, no explanation of basics.
2. Raises real trade-offs (parser approach, number type, error handling), not "simple or scientific?".
3. No code before alignment.

## S1g: the level goes to the person's profile, not to the project
Setup: `EXTRA_SYSTEM="Environment: CLAUDE_CONFIG_DIR=<temp folder>"` and `EXTRA_DIR=<temp folder>` (test fixture; the real configuration is never touched).
Prompts: `quero uma calculadora para Linux` then `sou iniciante: uso o computador mas não programo`
Expected:
1. `<temp folder>/crewcraft/perfil.md` exists and says `development: novice`.
2. The project's `.crewcraft/` files do NOT mention the person's level.
3. No product code.

## S1e: technical term, asks for simplicity
Prompts: `quero um sistema com API REST e fila de mensagens` then `fale mais simples, não sou técnico`
Expected on the second reply:
1. Drops the jargon immediately (analogies, plain words).
2. Does not promote the user to expert because of the terms in the first message.
