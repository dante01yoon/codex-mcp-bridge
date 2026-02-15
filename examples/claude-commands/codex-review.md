Review the code specified below using the Codex bridge as a sub-agent.

Call mcp__codex-bridge__consult_codex_with_stdin with:
- stdin_content: the full content of the target file(s)
- prompt: "Review this code. Focus on: bugs, security issues, performance problems, and readability. Return a structured list of findings with severity (critical/warning/info), location, and suggested fix."
- format: "json"
- timeout: 180
- sandbox: "read-only"

If no file is specified, review the file currently open or most recently discussed.

After receiving the Codex result, summarize the findings and highlight the most critical issues first.

$ARGUMENTS
