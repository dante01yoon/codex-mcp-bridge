Explain the code specified below using the Codex bridge as a sub-agent.

First, read the target file(s). Then call mcp__codex-bridge__consult_codex_with_stdin with:
- stdin_content: the full content of the target file(s)
- prompt: "Explain this code clearly and concisely. Cover: 1) What it does (purpose), 2) How it works (key logic flow), 3) Important design decisions, 4) Potential gotchas or non-obvious behavior. Use plain language."
- format: "text"
- timeout: 180
- sandbox: "read-only"

After receiving the Codex result, present the explanation. Add any additional context from the broader project if relevant.

$ARGUMENTS
