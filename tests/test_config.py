import json
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


def test_settings_load_from_json_file(monkeypatch, tmp_path: Path) -> None:
    """JSON config file values are used when env vars are not set."""
    config = {
        "default_timeout": 200,
        "default_sandbox": "workspace-write",
        "default_model": "o3",
        "max_output_chars": 5000,
        "allowed_dirs": [str(tmp_path)],
    }
    config_file = tmp_path / "codex-bridge.json"
    config_file.write_text(json.dumps(config))

    # Clear env vars so file takes effect
    monkeypatch.delenv("CODEX_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("CODEX_DEFAULT_TIMEOUT", raising=False)
    monkeypatch.delenv("CODEX_DEFAULT_SANDBOX", raising=False)
    monkeypatch.delenv("CODEX_ALLOWED_DIRS", raising=False)
    monkeypatch.delenv("CODEX_MAX_OUTPUT_CHARS", raising=False)

    # Patch cwd so the config file is found
    monkeypatch.chdir(tmp_path)

    settings = Settings.load()
    assert settings.default_model == "o3"
    assert settings.default_timeout == 200
    assert settings.default_sandbox == SandboxMode.WORKSPACE_WRITE
    assert settings.max_output_chars == 5000
    assert tmp_path.resolve() in settings.allowed_dirs


def test_settings_env_overrides_json(monkeypatch, tmp_path: Path) -> None:
    """Environment variables take precedence over JSON config file."""
    config = {"default_timeout": 200, "default_sandbox": "workspace-write"}
    config_file = tmp_path / "codex-bridge.json"
    config_file.write_text(json.dumps(config))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CODEX_DEFAULT_TIMEOUT", "300")
    monkeypatch.delenv("CODEX_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("CODEX_DEFAULT_SANDBOX", raising=False)
    monkeypatch.delenv("CODEX_ALLOWED_DIRS", raising=False)
    monkeypatch.delenv("CODEX_MAX_OUTPUT_CHARS", raising=False)

    settings = Settings.load()
    assert settings.default_timeout == 300  # env wins
    assert settings.default_sandbox == SandboxMode.WORKSPACE_WRITE  # file used


def test_settings_load_no_config_file_uses_defaults(monkeypatch, tmp_path: Path) -> None:
    """When no config file exists and no env vars, defaults are used."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODEX_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("CODEX_DEFAULT_TIMEOUT", raising=False)
    monkeypatch.delenv("CODEX_DEFAULT_SANDBOX", raising=False)
    monkeypatch.delenv("CODEX_ALLOWED_DIRS", raising=False)
    monkeypatch.delenv("CODEX_MAX_OUTPUT_CHARS", raising=False)

    settings = Settings.load()
    assert settings.default_model is None
    assert settings.default_timeout == 90
    assert settings.default_sandbox == SandboxMode.READ_ONLY
    assert settings.max_output_chars == 12000


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


# --- Missing tests generated via Codex bridge ---


def test_read_int_env_clamps_below_minimum(monkeypatch) -> None:
    from codex_bridge_mcp.config import _read_int_env

    monkeypatch.setenv("CODEX_TEST_INT", "0")
    assert _read_int_env("CODEX_TEST_INT", default=90, minimum=5) == 5


def test_parse_allowed_dirs_empty_and_multiple_with_spaces(tmp_path: Path) -> None:
    from codex_bridge_mcp.config import _parse_allowed_dirs

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    assert _parse_allowed_dirs("") == []
    raw = f"  {first}  ,   {second}   "
    assert _parse_allowed_dirs(raw) == [first.resolve(), second.resolve()]


def test_load_json_config_malformed_returns_empty_dict(tmp_path: Path) -> None:
    from codex_bridge_mcp.config import _load_json_config

    bad = tmp_path / "bad.json"
    bad.write_text("{not-valid-json", encoding="utf-8")

    assert _load_json_config(bad) == {}


def test_load_json_config_non_dict_returns_empty_dict(tmp_path: Path) -> None:
    from codex_bridge_mcp.config import _load_json_config

    arr = tmp_path / "array.json"
    arr.write_text('["a", "b"]', encoding="utf-8")

    assert _load_json_config(arr) == {}


def test_resolve_directory_rejects_nonexistent_directory(tmp_path: Path) -> None:
    settings = Settings()
    with pytest.raises(ValueError, match="Directory does not exist"):
        resolve_directory("does-not-exist", settings, base_dir=tmp_path)


def test_truncate_output_empty_string() -> None:
    assert truncate_output("", 100) == ""


def test_settings_load_non_list_allowed_dirs_in_json(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for key in (
        "CODEX_DEFAULT_MODEL",
        "CODEX_DEFAULT_TIMEOUT",
        "CODEX_DEFAULT_SANDBOX",
        "CODEX_ALLOWED_DIRS",
        "CODEX_MAX_OUTPUT_CHARS",
    ):
        monkeypatch.delenv(key, raising=False)

    config_file = tmp_path / "codex-bridge.json"
    config_file.write_text('{"allowed_dirs": "/tmp/not-a-list"}', encoding="utf-8")

    settings = Settings.load()
    assert settings.allowed_dirs == []
