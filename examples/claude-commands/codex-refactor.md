Refactor the specified code using the Codex bridge as a sub-agent.

First, read the target file(s). Then call mcp__codex-bridge__consult_codex_with_stdin with:
- stdin_content: the full content of the target file(s)
- prompt: "Refactor this code to improve readability, maintainability, and structure. Preserve all existing behavior. Apply these principles: extract repeated logic, simplify conditionals, improve naming, reduce nesting. Return the complete refactored code."
- format: "code"
- timeout: 180
- sandbox: "workspace-write"

After receiving the Codex result, show the diff between original and refactored code. Apply the changes only after confirming the refactoring intent with the user.

$ARGUMENTS
