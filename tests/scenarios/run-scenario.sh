#!/usr/bin/env bash
# Usage: run-scenario.sh <id> <baseline|plugin> "<prompt>" ["<next prompt>" ...]
# Runs Claude headless in an empty scratch project. User plugins and MCP servers are off.
set -u
ID="$1"; MODE="$2"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$HERE/../.." && pwd)"
OUT="$HERE/results"; mkdir -p "$OUT"
WORK="$(mktemp -d -p "${SCRATCH:-${TMPDIR:-/tmp}}")"
cd "$WORK" || exit 1
FLAGS=(--setting-sources project --strict-mcp-config --disallowedTools NotebookEdit --allowedTools "Bash(python:*)"
       --permission-mode acceptEdits --max-turns "${MAX_TURNS:-4}" --output-format text --max-budget-usd 1.5)
[ "$MODE" = plugin ] && FLAGS+=(--plugin-dir "$PLUGIN" --add-dir "$PLUGIN")
[ -n "${EXTRA_DIR:-}" ] && FLAGS+=(--add-dir "$EXTRA_DIR")
[ -n "${EXTRA_SYSTEM:-}" ] && FLAGS+=(--append-system-prompt "$EXTRA_SYSTEM")
SESSION="$(python -c 'import uuid;print(uuid.uuid4())')"
FIRST=1
RESULT="$OUT/$ID-$MODE.txt"
echo "### WORKDIR: $WORK" > "$RESULT"
for PROMPT in "$@"; do
  if [ "$FIRST" = 1 ]; then ARGS=(--session-id "$SESSION"); FIRST=0; else ARGS=(--resume "$SESSION"); fi
  { echo "### PROMPT: $PROMPT"; claude -p "$PROMPT" "${FLAGS[@]}" "${ARGS[@]}" 2>&1; echo; } >> "$RESULT"
done
{ echo "### FILES CREATED:"; find . -type f -not -path './.git/*' | head -50; } >> "$RESULT"
echo "done $ID $MODE"
