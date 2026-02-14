import subprocess
from pathlib import Path

from codex_bridge_mcp.config import Settings
from codex_bridge_mcp.runner import CodexRequest, run_codex
from codex_bridge_mcp.types import OutputFormat, SandboxMode


class _Completed:
    def __init__(self, code: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def test_run_codex_missing_binary(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: None)
    result = run_codex(CodexRequest(query="hello"), Settings())
    assert "not found" in result.lower()


def test_run_codex_timeout(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")

    def _boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="codex", timeout=1)

    monkeypatch.setattr("codex_bridge_mcp.runner.subprocess.run", _boom)

    settings = Settings()
    result = run_codex(CodexRequest(query="hello", directory=".", timeout=1), settings)
    assert "timed out" in result.lower()


def test_run_codex_nonzero_exit(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    monkeypatch.setattr(
        "codex_bridge_mcp.runner.subprocess.run",
        lambda *_a, **_k: _Completed(code=2, stderr="permission denied"),
    )

    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert "exited with code 2" in result.lower()


def test_run_codex_nonzero_exit_truncates_stderr(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    very_long_stderr = "e" * 3000
    monkeypatch.setattr(
        "codex_bridge_mcp.runner.subprocess.run",
        lambda *_a, **_k: _Completed(code=3, stderr=very_long_stderr),
    )

    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert "stderr truncated" in result.lower()


def test_run_codex_auth_failure_hint(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    monkeypatch.setattr(
        "codex_bridge_mcp.runner.subprocess.run",
        lambda *_a, **_k: _Completed(code=1, stderr="not logged in, please login"),
    )

    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert "codex login" in result


def test_run_codex_uses_output_file_before_stdout(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")

    def _fake_run(cmd, *_a, **_k):
        output_index = cmd.index("--output-last-message") + 1
        Path(cmd[output_index]).write_text("from-file", encoding="utf-8")
        return _Completed(code=0, stdout="from-stdout")

    monkeypatch.setattr("codex_bridge_mcp.runner.subprocess.run", _fake_run)
    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert result == "from-file"


def test_run_codex_uses_stdout_fallback(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    monkeypatch.setattr(
        "codex_bridge_mcp.runner.subprocess.run",
        lambda *_a, **_k: _Completed(code=0, stdout="from-stdout"),
    )

    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert result == "from-stdout"


def test_run_codex_returns_error_for_empty_output(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    monkeypatch.setattr(
        "codex_bridge_mcp.runner.subprocess.run",
        lambda *_a, **_k: _Completed(code=0, stdout="   "),
    )

    result = run_codex(CodexRequest(query="hello", directory="."), Settings())
    assert "produced no output" in result.lower()


def test_run_codex_request_values_override_settings(monkeypatch) -> None:
    monkeypatch.setattr("codex_bridge_mcp.runner.shutil.which", lambda _name: "/usr/bin/codex")
    captured = {}

    def _fake_run(cmd, *_a, **kwargs):
        captured["cmd"] = cmd
        captured["timeout"] = kwargs["timeout"]
        return _Completed(code=0, stdout="ok")

    monkeypatch.setattr("codex_bridge_mcp.runner.subprocess.run", _fake_run)

    settings = Settings(
        default_model="settings-model",
        default_timeout=60,
        default_sandbox=SandboxMode.READ_ONLY,
    )
    request = CodexRequest(
        query="hello",
        directory=".",
        format=OutputFormat.JSON,
        timeout=7,
        model="request-model",
        sandbox=SandboxMode.WORKSPACE_WRITE,
    )
    result = run_codex(request, settings)

    assert result == "ok"
    assert captured["timeout"] == 7
    assert "--model" in captured["cmd"]
    model_index = captured["cmd"].index("--model") + 1
    assert captured["cmd"][model_index] == "request-model"
    sandbox_index = captured["cmd"].index("--sandbox") + 1
    assert captured["cmd"][sandbox_index] == SandboxMode.WORKSPACE_WRITE.value
