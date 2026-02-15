Generate new code using the Codex bridge as a sub-agent.

Call mcp__codex-bridge__consult_codex with:
- query: the generation task described in $ARGUMENTS. Include context about the project's tech stack, conventions, and where the generated code will be used.
- directory: current working directory
- format: "code"
- timeout: 180
- sandbox: "workspace-write"

If additional context is needed (existing types, interfaces, or related code), read those files first and use mcp__codex-bridge__consult_codex_with_stdin instead, passing the context as stdin_content.

After receiving the Codex result, write the generated code to the appropriate file location. Follow the project's existing file structure and naming conventions.

$ARGUMENTS
