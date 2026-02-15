---
name: Codex Generate
description: Delegates new code generation to Codex. Gathers project context and generates code following existing conventions.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: Describe what code to generate
---

Generate new code using Codex as a sub-agent.

## Steps

1. If additional context is needed (existing types, interfaces, or related code), read those files first.
2. Call the appropriate Codex tool:
   - **Without context**: `mcp__codex-bridge__consult_codex` with:
     - `query`: the generation task described in the arguments, including context about the project's tech stack, conventions, and where the generated code will be used
     - `format`: "code"
     - `timeout`: 180
     - `sandbox`: "workspace-write"
   - **With context**: `mcp__codex-bridge__consult_codex_with_stdin` with:
     - `stdin_content`: the related code/types/interfaces
     - `prompt`: the generation task with explicit constraints
     - `format`: "code"
     - `timeout`: 180
     - `sandbox`: "workspace-write"
3. Write the generated code to the appropriate file location following the project's existing file structure and naming conventions.

$ARGUMENTS
