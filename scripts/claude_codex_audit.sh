#!/usr/bin/env bash
set -euo pipefail

# Audit launcher: runs Claude in stream-json mode, then summarizes
# whether codex-bridge MCP tools were actually used.

DEFAULT_APPEND_PROMPT='For coding and technical tasks, call mcp__codex-bridge__consult_codex first. If the input is large (diff/log/file content), call mcp__codex-bridge__consult_codex_with_stdin. Use explicit tool arguments with sandbox read-only and timeout 180 unless the task requires otherwise.'
DEFAULT_ALLOWED_TOOLS='mcp__codex-bridge__consult_codex,mcp__codex-bridge__consult_codex_with_stdin'
DEFAULT_PERMISSION_MODE='dontAsk'

APPEND_PROMPT="${CLAUDE_CODEX_APPEND_PROMPT:-$DEFAULT_APPEND_PROMPT}"
ALLOWED_TOOLS="${CLAUDE_CODEX_ALLOWED_TOOLS:-$DEFAULT_ALLOWED_TOOLS}"
PERMISSION_MODE="${CLAUDE_CODEX_PERMISSION_MODE:-$DEFAULT_PERMISSION_MODE}"

if [[ $# -eq 0 ]]; then
  cat <<'USAGE'
Usage:
  claude_codex_audit.sh "<prompt>"
  claude_codex_audit.sh -- "<prompt>"

Environment overrides:
  CLAUDE_CODEX_APPEND_PROMPT
  CLAUDE_CODEX_ALLOWED_TOOLS
  CLAUDE_CODEX_PERMISSION_MODE
USAGE
  exit 1
fi

RAW_OUTPUT_FILE="$(mktemp /tmp/claude-codex-audit-XXXX.jsonl)"
cleanup() {
  rm -f "$RAW_OUTPUT_FILE"
}
trap cleanup EXIT

claude \
  -p \
  --verbose \
  --output-format stream-json \
  --permission-mode "$PERMISSION_MODE" \
  --append-system-prompt "$APPEND_PROMPT" \
  --allowedTools "$ALLOWED_TOOLS" \
  "$@" >"$RAW_OUTPUT_FILE"

python3 - "$RAW_OUTPUT_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
tools = []
final_result = None

with open(path, "r", encoding="utf-8") as f:
    for raw in f:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "assistant":
            message = event.get("message", {})
            for block in message.get("content", []):
                if block.get("type") == "tool_use":
                    name = block.get("name", "")
                    if name:
                        tools.append(name)

        if event.get("type") == "result":
            final_result = event.get("result")

deduped_tools = list(dict.fromkeys(tools))
codex_tools = [t for t in deduped_tools if t.startswith("mcp__codex-bridge__")]

print("=== Claude Result ===")
if isinstance(final_result, str):
    print(final_result)
elif final_result is None:
    print("(no result found)")
else:
    print(json.dumps(final_result, ensure_ascii=False))

print("\n=== Tool Audit ===")
if deduped_tools:
    print("tools_used:", ", ".join(deduped_tools))
else:
    print("tools_used: (none)")

print("codex_bridge_used:", "yes" if codex_tools else "no")
if codex_tools:
    print("codex_bridge_tools:", ", ".join(codex_tools))
PY
