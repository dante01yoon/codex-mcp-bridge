---
name: Codex Ask
description: Delegates a general question to Codex and returns the answer. Use for technical questions, research, or analysis.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex
context: fork
argument-hint: Your question for Codex
---

Delegate the question below to Codex and return the answer.

## Steps

1. Call `mcp__codex-bridge__consult_codex` with:
   - `query`: the user's question from the arguments
   - `format`: "text"
   - `timeout`: 180
   - `sandbox`: "read-only"
2. Return the Codex result directly, adding your own commentary only if the result needs clarification or correction.

$ARGUMENTS
