#!/usr/bin/env bash
set -euo pipefail

# Default launcher for Codex-first usage in Claude CLI.
# You can override defaults with environment variables below.
DEFAULT_APPEND_PROMPT='For coding and technical tasks, call mcp__codex-bridge__consult_codex first. If the input is large (diff/log/file content), call mcp__codex-bridge__consult_codex_with_stdin. Use explicit tool arguments with sandbox read-only and timeout 180 unless the task requires otherwise.'
DEFAULT_ALLOWED_TOOLS='mcp__codex-bridge__consult_codex,mcp__codex-bridge__consult_codex_with_stdin'

APPEND_PROMPT="${CLAUDE_CODEX_APPEND_PROMPT:-$DEFAULT_APPEND_PROMPT}"
ALLOWED_TOOLS="${CLAUDE_CODEX_ALLOWED_TOOLS:-$DEFAULT_ALLOWED_TOOLS}"

exec claude \
  --append-system-prompt "$APPEND_PROMPT" \
  --allowedTools "$ALLOWED_TOOLS" \
  "$@"
