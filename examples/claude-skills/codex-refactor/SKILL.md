---
name: Codex Refactor
description: Delegates code refactoring to Codex. Reads target code, sends for structural improvement while preserving behavior, and shows diff before applying.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: File path and refactoring goals
---

Refactor the specified code using Codex as a sub-agent.

## Steps

1. Read the target file(s) specified in the arguments.
2. Call `mcp__codex-bridge__consult_codex_with_stdin` with:
   - `stdin_content`: the full content of the target file(s)
   - `prompt`: "Refactor this code to improve readability, maintainability, and structure. Preserve all existing behavior. Apply these principles: extract repeated logic, simplify conditionals, improve naming, reduce nesting. Return the complete refactored code."
   - `format`: "code"
   - `timeout`: 180
   - `sandbox`: "workspace-write"
3. Show the diff between original and refactored code.
4. Apply changes only after the user confirms the refactoring intent.

$ARGUMENTS
