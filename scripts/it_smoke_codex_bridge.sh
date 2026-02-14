#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v codex >/dev/null 2>&1; then
  echo "FAIL: codex CLI not found in PATH"
  exit 1
fi

uv run --with . python - <<'PY'
import asyncio

from codex_bridge_mcp.server import (
    ConsultCodexInput,
    ConsultCodexWithStdinInput,
    consult_codex,
    consult_codex_with_stdin,
)
from codex_bridge_mcp.types import OutputFormat, SandboxMode


async def main() -> None:
    r1 = await consult_codex(
        ConsultCodexInput(
            query='Return a compact JSON object with key "status" and value "ok".',
            directory='.',
            format=OutputFormat.JSON,
            timeout=45,
            sandbox=SandboxMode.READ_ONLY,
        )
    )
    print("consult_codex:", (r1[:240] + "...") if len(r1) > 240 else r1)

    r2 = await consult_codex_with_stdin(
        ConsultCodexWithStdinInput(
            stdin_content='ERROR: test_login failed with AssertionError at line 42',
            prompt='Based on INPUT, propose one likely root cause and one test improvement in JSON.',
            directory='.',
            format=OutputFormat.JSON,
            timeout=60,
            sandbox=SandboxMode.READ_ONLY,
        )
    )
    print("consult_codex_with_stdin:", (r2[:240] + "...") if len(r2) > 240 else r2)


asyncio.run(main())
PY
