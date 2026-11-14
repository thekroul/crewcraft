# S2: visual scenarios (skill `prototipo-visual`)

Run with `tests/scenarios/run-scenario.sh`. For S2c set `EXTRA_DIR` to the folder that holds the reference image.
A scenario passes only when EVERY expected behavior is present in the plugin run.

## S2a: dashboard request, look not yet decided
Prompt: `Já decidimos o que é: um painel para a equipe de suporte acompanhar chamados, usado por técnicos no Windows. Preciso ver o visual antes de você construir qualquer coisa.`
Expected:
1. Creates exactly 3 structure mockups under `.crewcraft/prototipos/`, different in structure.
2. The structure files contain no color values (only `var(--...)`) and link a theme file.
3. Sample data looks real (no round placeholder numbers).
4. Asks which structure is closest, one question. No product code.

## S2b: rejects the look
Prompts: S2a prompt, then `não gostei das cores, parece feito por IA`
Expected on the second reply:
1. Structure files are unchanged; only a theme is previewed or new theme files appear.
2. Proposes a really different direction (restrained palette, flat, dense), not a small tweak.
3. Asks for a reference print.
4. `ficha-visual.md` gains a line about what was disliked.

## S2c: reference image pasted
Prompt: `Gostei do estilo deste painel como referência: <image path>. Quero algo nessa linha para o painel de chamados, mas não quero uma cópia.`
Expected:
1. Describes qualities (few colors, flat, density, real data), not a pixel copy.
2. States that it takes qualities, not the design.
3. Saves qualities in `ficha-visual.md`.
4. Does not download anything from the internet.
