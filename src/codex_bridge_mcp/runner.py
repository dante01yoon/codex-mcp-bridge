from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import shutil

from pydantic import BaseModel, ConfigDict, Field

from codex_bridge_mcp.config import Settings, resolve_directory, truncate_output
from codex_bridge_mcp.types import OutputFormat, SandboxMode

MAX_STDERR_CHARS = 2000


class CodexRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=1)
    directory: str = "."
    format: OutputFormat = OutputFormat.JSON
    timeout: int | None = Field(default=None, ge=1)
    model: str | None = None
    sandbox: SandboxMode | None = None


def _build_query(user_query: str, output_format: OutputFormat) -> str:
    if output_format == OutputFormat.JSON:
        hint = "Return only valid JSON with no markdown fences or explanation."
    elif output_format == OutputFormat.CODE:
        hint = "Return only code output. Avoid commentary unless absolutely necessary."
    else:
        hint = "Return a concise plain-text answer."
    return f"{hint}\n\nTASK:\n{user_query}"


def _stderr_excerpt(stderr: str) -> str:
    text = (stderr or "").strip()
    if len(text) <= MAX_STDERR_CHARS:
        return text
    return text[:MAX_STDERR_CHARS] + "...(stderr truncated)"


def _auth_hint(stderr: str) -> bool:
    lowered = (stderr or "").lower()
    markers = ["login", "authenticate", "auth", "credential", "not logged in"]
    return any(marker in lowered for marker in markers)


def run_codex(request: CodexRequest, settings: Settings) -> str:
    codex_path = shutil.which("codex")
    if not codex_path:
        return "Error: `codex` CLI not found in PATH. Install Codex CLI and retry."

    try:
        target_dir = resolve_directory(request.directory, settings)
    except ValueError as exc:
        return f"Error: {exc}"

    timeout = request.timeout or settings.default_timeout
    model = request.model or settings.default_model
    sandbox = request.sandbox or settings.default_sandbox
    query = _build_query(request.query, request.format)

    with tempfile.NamedTemporaryFile(prefix="codex_bridge_", suffix=".txt", delete=False) as temp_file:
        output_file = Path(temp_file.name)

    cmd = [
        codex_path,
        "exec",
        "-",
        "--skip-git-repo-check",
        "--sandbox",
        sandbox.value,
        "-C",
        str(target_dir),
        "--output-last-message",
        str(output_file),
    ]
    if model:
        cmd.extend(["--model", model])

    try:
        completed = subprocess.run(
            cmd,
            input=query,
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=target_dir,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Error: Codex timed out after {timeout} seconds."

    try:
        if completed.returncode != 0:
            stderr = _stderr_excerpt(completed.stderr)
            if _auth_hint(stderr):
                return (
                    "Error: Codex authentication appears unavailable. "
                    "Run `codex login` and retry."
                )
            detail = f" stderr: {stderr}" if stderr else ""
            return f"Error: Codex exited with code {completed.returncode}.{detail}"

        output = ""
        try:
            output = output_file.read_text(encoding="utf-8").strip()
        except OSError:
            output = ""

        if not output:
            output = (completed.stdout or "").strip()

        if not output:
            return "Error: Codex produced no output."

        return truncate_output(output, settings.max_output_chars)
    finally:
        output_file.unlink(missing_ok=True)
