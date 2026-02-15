from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from codex_bridge_mcp.types import SandboxMode

CONFIG_FILE_NAMES = ("codex-bridge.json", ".codex-bridge.json")


def _read_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


def _parse_allowed_dirs(raw: str | None) -> list[Path]:
    if not raw:
        return []
    out: list[Path] = []
    for item in raw.split(","):
        candidate = item.strip()
        if not candidate:
            continue
        out.append(Path(candidate).expanduser().resolve())
    return out


def _find_config_file() -> Path | None:
    """Search for a JSON config file in known locations."""
    search_paths = (Path.cwd(), Path.home() / ".config" / "codex-bridge")
    for search_dir in search_paths:
        for name in CONFIG_FILE_NAMES:
            candidate = search_dir / name
            if candidate.is_file():
                return candidate
    return None


def _load_json_config(path: Path) -> dict[str, Any]:
    """Load and return a JSON config file. Returns empty dict on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        print(f"Warning: failed to load config from {path}", file=sys.stderr)
        return {}


class Settings(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    default_model: str | None = None
    default_timeout: int = Field(default=90, ge=1)
    default_sandbox: SandboxMode = SandboxMode.READ_ONLY
    allowed_dirs: list[Path] = Field(default_factory=list)
    max_output_chars: int = Field(default=12000, ge=512)

    @classmethod
    def load(cls) -> "Settings":
        """Load settings with precedence: env var > config file > defaults."""

        # 1. Load JSON config file (lowest precedence)
        file_config: dict[str, Any] = {}
        config_path = _find_config_file()
        if config_path is not None:
            file_config = _load_json_config(config_path)

        # 2. Resolve each setting: env var > config file > default
        # -- default_model
        default_model = os.getenv("CODEX_DEFAULT_MODEL") or file_config.get("default_model") or None

        # -- default_timeout
        env_timeout = os.getenv("CODEX_DEFAULT_TIMEOUT")
        if env_timeout is not None:
            default_timeout = _read_int_env("CODEX_DEFAULT_TIMEOUT", 90)
        elif "default_timeout" in file_config:
            raw = file_config["default_timeout"]
            default_timeout = max(int(raw), 1) if isinstance(raw, (int, float)) else 90
        else:
            default_timeout = 90

        # -- default_sandbox
        env_sandbox = os.getenv("CODEX_DEFAULT_SANDBOX")
        sandbox_raw = env_sandbox or file_config.get("default_sandbox") or SandboxMode.READ_ONLY.value
        try:
            default_sandbox = SandboxMode(sandbox_raw)
        except ValueError:
            default_sandbox = SandboxMode.READ_ONLY

        # -- allowed_dirs
        env_dirs = os.getenv("CODEX_ALLOWED_DIRS")
        if env_dirs is not None:
            allowed_dirs = _parse_allowed_dirs(env_dirs)
        elif "allowed_dirs" in file_config:
            raw_dirs = file_config["allowed_dirs"]
            if isinstance(raw_dirs, list):
                allowed_dirs = [Path(d).expanduser().resolve() for d in raw_dirs if isinstance(d, str)]
            else:
                allowed_dirs = []
        else:
            allowed_dirs = []

        # -- max_output_chars
        env_max = os.getenv("CODEX_MAX_OUTPUT_CHARS")
        if env_max is not None:
            max_output_chars = _read_int_env("CODEX_MAX_OUTPUT_CHARS", 12000, minimum=512)
        elif "max_output_chars" in file_config:
            raw = file_config["max_output_chars"]
            max_output_chars = max(int(raw), 512) if isinstance(raw, (int, float)) else 12000
        else:
            max_output_chars = 12000

        return cls(
            default_model=default_model,
            default_timeout=default_timeout,
            default_sandbox=default_sandbox,
            allowed_dirs=allowed_dirs,
            max_output_chars=max_output_chars,
        )

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables only (legacy)."""
        return cls.load()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _within_any(path: Path, bases: Iterable[Path]) -> bool:
    return any(_is_relative_to(path, base) for base in bases)


def resolve_directory(directory: str, settings: Settings, base_dir: Path | None = None) -> Path:
    root = (base_dir or Path.cwd()).resolve()
    requested = Path(directory).expanduser()
    target = (root / requested).resolve() if not requested.is_absolute() else requested.resolve()

    if not target.exists() or not target.is_dir():
        raise ValueError(f"Directory does not exist: {target}")

    if settings.allowed_dirs:
        if not _within_any(target, settings.allowed_dirs):
            allowed = ", ".join(str(p) for p in settings.allowed_dirs)
            raise ValueError(
                f"Directory is outside CODEX_ALLOWED_DIRS: {target}. Allowed: {allowed}"
            )
    elif not _is_relative_to(target, root):
        raise ValueError(f"Directory is outside current workspace: {target}")

    return target


def truncate_output(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...(truncated)"
