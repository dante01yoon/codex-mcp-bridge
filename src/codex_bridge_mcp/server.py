from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from codex_bridge_mcp.config import Settings
from codex_bridge_mcp.runner import CodexRequest, run_codex
from codex_bridge_mcp.types import OutputFormat, SandboxMode


_SETTINGS = Settings.from_env()
mcp = FastMCP("codex_bridge_mcp")


class ConsultCodexInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=1, description="Task prompt for Codex")
    directory: str = Field(default=".", description="Working directory for codex exec")
    format: OutputFormat = Field(
        default=OutputFormat.JSON,
        description="Preferred output format: text, json, or code",
    )
    timeout: int | None = Field(
        default=None,
        ge=1,
        description="Timeout seconds. If omitted, uses env/default setting.",
    )
    model: str | None = Field(default=None, description="Optional Codex model override")
    sandbox: SandboxMode | None = Field(
        default=None,
        description="Sandbox mode override: read-only/workspace-write/danger-full-access",
    )


class ConsultCodexWithStdinInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    stdin_content: str = Field(..., min_length=1, description="Large input content")
    prompt: str = Field(..., min_length=1, description="Task instruction")
    directory: str = Field(default=".")
    format: OutputFormat = Field(default=OutputFormat.JSON)
    timeout: int | None = Field(default=None, ge=1)
    model: str | None = Field(default=None)
    sandbox: SandboxMode | None = Field(default=None)


@mcp.tool(
    name="consult_codex",
    annotations={
        "title": "Consult Codex",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def consult_codex(params: ConsultCodexInput) -> str:
    """Run codex exec with a single prompt and return the final output text."""

    request = CodexRequest(
        query=params.query,
        directory=params.directory,
        format=params.format,
        timeout=params.timeout,
        model=params.model,
        sandbox=params.sandbox,
    )
    return run_codex(request, _SETTINGS)


@mcp.tool(
    name="consult_codex_with_stdin",
    annotations={
        "title": "Consult Codex With Input",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def consult_codex_with_stdin(params: ConsultCodexWithStdinInput) -> str:
    """Run codex exec using large input content plus a task prompt."""

    wrapped_query = (
        "INPUT:\n"
        "<<<BEGIN_INPUT\n"
        f"{params.stdin_content}\n"
        "END_INPUT>>>\n\n"
        "TASK:\n"
        f"{params.prompt}"
    )
    request = CodexRequest(
        query=wrapped_query,
        directory=params.directory,
        format=params.format,
        timeout=params.timeout,
        model=params.model,
        sandbox=params.sandbox,
    )
    return run_codex(request, _SETTINGS)


def main() -> None:
    """Entrypoint for stdio MCP transport."""

    # Never print to stdout; MCP protocol uses stdout.
    if sys.stdout.closed:
        raise RuntimeError("stdout is unavailable")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
