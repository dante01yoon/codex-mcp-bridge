---
name: Codex Fix
description: Delegates bug fixing to Codex. Reads the broken code, sends it for repair, and applies the fix with a diff preview.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: File path and description of the bug to fix
---

Fix the bug or issue in the specified code using Codex as a sub-agent.

## Steps

1. Read the target file(s) mentioned in the arguments.
2. Call `mcp__codex-bridge__consult_codex_with_stdin` with:
   - `stdin_content`: the full content of the target file(s)
   - `prompt`: "Fix the following issue in this code: [ISSUE]. Return the complete fixed code with no omissions. Add a brief comment at each fix location explaining what was changed and why."
   - `format`: "code"
   - `timeout`: 180
   - `sandbox`: "workspace-write"
3. Replace `[ISSUE]` with the user's description from the arguments. If no specific issue is described, analyze the code for obvious bugs, type errors, and logic issues.
4. Show the diff of changes before applying.
5. Apply the fix to the original file.

$ARGUMENTS
