---
name: Codex Review
description: Delegates code review to Codex. Reads target files and sends them for analysis focusing on bugs, security, performance, and readability.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: File path or description of code to review
---

Review the code specified below using Codex as a sub-agent.

## Steps

1. Read the target file(s) specified in the arguments. If no file is specified, ask the user.
2. Call `mcp__codex-bridge__consult_codex_with_stdin` with:
   - `stdin_content`: the full content of the target file(s)
   - `prompt`: "Review this code. Focus on: bugs, security issues, performance problems, and readability. Return a structured list of findings with severity (critical/warning/info), location, and suggested fix."
   - `format`: "json"
   - `timeout`: 180
   - `sandbox`: "read-only"
3. Summarize findings, highlighting the most critical issues first.

$ARGUMENTS
