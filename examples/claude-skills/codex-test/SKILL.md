---
name: Codex Test
description: Delegates test generation to Codex. Reads source code and generates comprehensive unit tests matching the project's testing framework.
user-invocable: true
allowed-tools:
  - mcp__codex-bridge__consult_codex_with_stdin
  - Read
  - Glob
  - Grep
context: fork
argument-hint: File path to generate tests for
---

Generate tests for the specified code using Codex as a sub-agent.

## Steps

1. Read the target file(s) specified in the arguments.
2. Detect the project's testing framework by checking existing test files, config, and dependencies.
3. Call `mcp__codex-bridge__consult_codex_with_stdin` with:
   - `stdin_content`: the full content of the target file(s)
   - `prompt`: "Generate comprehensive unit tests for this code. Include edge cases, error cases, and happy path. Use [FRAMEWORK] as the testing framework. Return only the test code."
   - `format`: "code"
   - `timeout`: 180
   - `sandbox`: "read-only"
4. Replace `[FRAMEWORK]` with the detected framework (pytest, vitest, jest, etc.).
5. Write the tests to the appropriate test file location following the project's test structure.

$ARGUMENTS
