---
name: Codex Explain
description: Delegates code explanation to Codex. Reads target code and returns a clear breakdown of purpose, logic flow, design decisions, and gotchas.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: File path or code to explain
---

Explain the specified code using Codex as a sub-agent.

## Steps

1. Read the target file(s) specified in the arguments.
2. Call `mcp__codex-bridge__consult_codex_with_stdin` with:
   - `stdin_content`: the full content of the target file(s)
   - `prompt`: "Explain this code clearly and concisely. Cover: 1) What it does (purpose), 2) How it works (key logic flow), 3) Important design decisions, 4) Potential gotchas or non-obvious behavior. Use plain language."
   - `format`: "text"
   - `timeout`: 180
   - `sandbox`: "read-only"
3. Present the explanation. Add any additional context from the broader project if relevant.

$ARGUMENTS
