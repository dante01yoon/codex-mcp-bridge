import asyncio

import pytest
from pydantic import ValidationError

from codex_bridge_mcp.server import (
    ConsultCodexInput,
    ConsultCodexWithStdinInput,
    consult_codex,
    consult_codex_with_stdin,
    main,
)
from codex_bridge_mcp.types import OutputFormat, SandboxMode


def test_consult_codex_input_validation() -> None:
    with pytest.raises(ValidationError):
        ConsultCodexInput(query="")


def test_consult_codex_maps_input_to_request(monkeypatch) -> None:
    captured = {}

    def _fake_run_codex(request, settings):
        captured["request"] = request
        captured["settings"] = settings
        return "ok"

    monkeypatch.setattr("codex_bridge_mcp.server.run_codex", _fake_run_codex)
    params = ConsultCodexInput(
        query="analyze",
        directory=".",
        format=OutputFormat.CODE,
        timeout=11,
        model="test-model",
        sandbox=SandboxMode.WORKSPACE_WRITE,
    )
    result = asyncio.run(consult_codex(params))

    assert result == "ok"
    assert captured["request"].query == "analyze"
    assert captured["request"].directory == "."
    assert captured["request"].format == OutputFormat.CODE
    assert captured["request"].timeout == 11
    assert captured["request"].model == "test-model"
    assert captured["request"].sandbox == SandboxMode.WORKSPACE_WRITE
    assert captured["settings"].default_sandbox is not None


def test_consult_codex_with_stdin_wraps_input_block(monkeypatch) -> None:
    captured = {}

    def _fake_run_codex(request, _settings):
        captured["request"] = request
        return "ok"

    monkeypatch.setattr("codex_bridge_mcp.server.run_codex", _fake_run_codex)
    params = ConsultCodexWithStdinInput(
        stdin_content="diff --git a b",
        prompt="create tests",
        directory=".",
        format=OutputFormat.JSON,
        timeout=20,
        model="test-model",
        sandbox=SandboxMode.READ_ONLY,
    )
    result = asyncio.run(consult_codex_with_stdin(params))

    assert result == "ok"
    wrapped_query = captured["request"].query
    assert "INPUT:" in wrapped_query
    assert "<<<BEGIN_INPUT" in wrapped_query
    assert "END_INPUT>>>" in wrapped_query
    assert "TASK:" in wrapped_query
    assert "diff --git a b" in wrapped_query
    assert "create tests" in wrapped_query


def test_main_keeps_stdout_clean(monkeypatch, capsys) -> None:
    called = {}

    def _fake_run(*, transport):
        called["transport"] = transport

    monkeypatch.setattr("codex_bridge_mcp.server.mcp.run", _fake_run)
    main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert called["transport"] == "stdio"


# --- Missing tests generated via Codex bridge ---


def test_consult_codex_with_stdin_input_rejects_empty_stdin_content() -> None:
    with pytest.raises(ValidationError):
        ConsultCodexWithStdinInput(stdin_content="   ", prompt="valid prompt")


def test_consult_codex_with_stdin_input_rejects_empty_prompt() -> None:
    with pytest.raises(ValidationError):
        ConsultCodexWithStdinInput(stdin_content="valid input", prompt="   ")


def test_consult_codex_input_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ConsultCodexInput(query="ok", unexpected="x")


def test_consult_codex_with_stdin_maps_all_parameters(monkeypatch) -> None:
    captured = {}

    def fake_run_codex(request, settings):
        captured["request"] = request
        captured["settings"] = settings
        return "ok"

    monkeypatch.setattr("codex_bridge_mcp.server.run_codex", fake_run_codex)

    params = ConsultCodexWithStdinInput(
        stdin_content="raw input",
        prompt="do something",
        directory="subdir",
        format=OutputFormat.CODE,
        timeout=17,
        model="gpt-test",
        sandbox=SandboxMode.WORKSPACE_WRITE,
    )

    result = asyncio.run(consult_codex_with_stdin(params))
    assert result == "ok"

    req = captured["request"]
    assert "<<<BEGIN_INPUT" in req.query
    assert "raw input" in req.query
    assert "END_INPUT>>>" in req.query
    assert "do something" in req.query
    assert req.directory == "subdir"
    assert req.format == OutputFormat.CODE
    assert req.timeout == 17
    assert req.model == "gpt-test"
    assert req.sandbox == SandboxMode.WORKSPACE_WRITE
