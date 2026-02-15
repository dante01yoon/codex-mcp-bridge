Generate tests for the code specified below using the Codex bridge as a sub-agent.

First, read the target file(s). Then call mcp__codex-bridge__consult_codex_with_stdin with:
- stdin_content: the full content of the target file(s)
- prompt: "Generate comprehensive unit tests for this code. Include edge cases, error cases, and happy path. Use the testing framework that matches the project (pytest for Python, vitest/jest for TypeScript). Return only the test code."
- format: "code"
- timeout: 180
- sandbox: "read-only"

After receiving the Codex result, write the tests to the appropriate test file location following the project's existing test structure.

$ARGUMENTS
