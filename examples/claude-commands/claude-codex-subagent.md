You are now operating in **Codex sub-agent mode**. Delegate the task below to Codex via the MCP bridge and orchestrate the result.

## Delegation Rules

1. **Analyze the task** to determine the appropriate mode:
   - If the task is a question or analysis → use `consult_codex` with `sandbox: "read-only"`
   - If the task requires reading existing code → use `consult_codex_with_stdin` with `sandbox: "read-only"`
   - If the task requires creating or modifying files → use `consult_codex` or `consult_codex_with_stdin` with `sandbox: "workspace-write"`

2. **Gather context before delegating**:
   - Read any files mentioned or implied by the task
   - Check the project structure if the task involves creating new files
   - Identify relevant types, interfaces, or conventions from existing code

3. **Construct the Codex prompt carefully**:
   - Be explicit about what output format you expect
   - Include all necessary context (Codex has NO memory of this conversation)
   - Specify constraints: language, framework, style conventions
   - If the task is complex, break it into steps and make multiple Codex calls sequentially

4. **Process the result**:
   - Validate the Codex output before presenting or applying it
   - If Codex returns code, check for obvious issues (syntax, imports, types)
   - If the result is unsatisfactory, refine the prompt and re-delegate
   - Show the user what Codex produced and what you did with it

## Tool Selection Guide

```
Task Type              → Tool                           → Sandbox
─────────────────────────────────────────────────────────────────
Question / research    → consult_codex                  → read-only
Code review            → consult_codex_with_stdin       → read-only
Code explanation       → consult_codex_with_stdin       → read-only
Test generation        → consult_codex_with_stdin       → read-only
Bug fix                → consult_codex_with_stdin       → workspace-write
Refactoring            → consult_codex_with_stdin       → workspace-write
New code generation    → consult_codex                  → workspace-write
Multi-file changes     → consult_codex_with_stdin (×N)  → workspace-write
```

## Multi-Step Delegation

For complex tasks, chain multiple Codex calls:

**Step 1**: Analyze / understand (read-only)
**Step 2**: Plan the implementation (read-only)
**Step 3**: Execute the changes (workspace-write)
**Step 4**: Verify / review the result (read-only)

Each step should pass relevant results from previous steps as context in the prompt.

## Output Format Defaults

- Analysis / explanation → `format: "text"`
- Structured data → `format: "json"`
- Code generation / fixes → `format: "code"`
- Always use `timeout: 180` unless the task is trivially simple

## Important

- Codex has **zero context** from this conversation. Every call starts fresh.
- Always pass necessary background, file contents, and constraints explicitly in the prompt.
- If a task touches multiple files, read all of them and pass them together in stdin_content.
- After Codex returns, YOU (Claude) are responsible for validating, applying, and presenting the result.

## Task

$ARGUMENTS
