Fix the bug or issue in the specified code using the Codex bridge as a sub-agent.

First, read the target file(s). Then call mcp__codex-bridge__consult_codex_with_stdin with:
- stdin_content: the full content of the target file(s)
- prompt: "Fix the following issue in this code: [ISSUE]. Return the complete fixed code with no omissions. Add a brief comment at each fix location explaining what was changed and why."
- format: "code"
- timeout: 180
- sandbox: "workspace-write"

Replace [ISSUE] with the user's description from $ARGUMENTS. If no specific issue is described, analyze the code for obvious bugs, type errors, and logic issues.

After receiving the Codex result, apply the fix to the original file. Show the diff of changes before writing.

$ARGUMENTS
