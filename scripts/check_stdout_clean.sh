#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv run --with . python - <<'PY'
import io
import contextlib

from codex_bridge_mcp import server

server.mcp.run = lambda **kwargs: None
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    server.main()

captured = buf.getvalue()
if captured:
    raise SystemExit(f"FAIL: stdout polluted: {captured!r}")

print("OK: stdout is clean for server.main()")
PY
