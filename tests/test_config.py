from pathlib import Path

import pytest

from codex_bridge_mcp.config import Settings, resolve_directory, truncate_output
from codex_bridge_mcp.types import SandboxMode


def test_settings_from_env_reads_values(monkeypatch, tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    monkeypatch.setenv("CODEX_DEFAULT_MODEL", "gpt-test")
    monkeypatch.setenv("CODEX_DEFAULT_TIMEOUT", "123")
    monkeypatch.setenv("CODEX_DEFAULT_SANDBOX", "workspace-write")
    monkeypatch.setenv("CODEX_ALLOWED_DIRS", str(allowed))
    monkeypatch.setenv("CODEX_MAX_OUTPUT_CHARS", "2048")

    settings = Settings.from_env()
    assert settings.default_model == "gpt-test"
    assert settings.default_timeout == 123
    assert settings.default_sandbox == SandboxMode.WORKSPACE_WRITE
    assert settings.allowed_dirs == [allowed.resolve()]
    assert settings.max_output_chars == 2048


def test_settings_invalid_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_DEFAULT_TIMEOUT", "invalid")
    monkeypatch.setenv("CODEX_DEFAULT_SANDBOX", "invalid")
    monkeypatch.setenv("CODEX_MAX_OUTPUT_CHARS", "invalid")

    settings = Settings.from_env()
    assert settings.default_timeout == 90
    assert settings.default_sandbox == SandboxMode.READ_ONLY
    assert settings.max_output_chars == 12000


def test_truncate_output_marks_truncated() -> None:
    result = truncate_output("abcdef", 3)
    assert result.startswith("abc")
    assert "(truncated)" in result


def test_truncate_output_keeps_exact_length() -> None:
    result = truncate_output("abcd", 4)
    assert result == "abcd"


def test_resolve_directory_rejects_outside_workspace(tmp_path: Path) -> None:
    inside = tmp_path / "inside"
    inside.mkdir()
    outside = tmp_path.parent

    settings = Settings(allowed_dirs=[])

    resolved_inside = resolve_directory(str(inside), settings, base_dir=tmp_path)
    assert resolved_inside == inside.resolve()

    with pytest.raises(ValueError, match="outside current workspace"):
        resolve_directory(str(outside), settings, base_dir=tmp_path)


def test_resolve_directory_allowlist_accepts_and_rejects(tmp_path: Path) -> None:
    allowed_root = tmp_path / "allowed"
    allowed_child = allowed_root / "child"
    denied = tmp_path / "denied"
    allowed_child.mkdir(parents=True)
    denied.mkdir()

    settings = Settings(allowed_dirs=[allowed_root.resolve()])
    resolved = resolve_directory(str(allowed_child), settings, base_dir=tmp_path)
    assert resolved == allowed_child.resolve()

    with pytest.raises(ValueError, match="outside CODEX_ALLOWED_DIRS"):
        resolve_directory(str(denied), settings, base_dir=tmp_path)
