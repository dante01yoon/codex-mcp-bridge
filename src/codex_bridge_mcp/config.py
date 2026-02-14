from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from codex_bridge_mcp.types import SandboxMode


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


class Settings(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    default_model: str | None = None
    default_timeout: int = Field(default=90, ge=1)
    default_sandbox: SandboxMode = SandboxMode.READ_ONLY
    allowed_dirs: list[Path] = Field(default_factory=list)
    max_output_chars: int = Field(default=12000, ge=512)

    @classmethod
    def from_env(cls) -> "Settings":
        sandbox_raw = os.getenv("CODEX_DEFAULT_SANDBOX", SandboxMode.READ_ONLY.value)
        try:
            sandbox = SandboxMode(sandbox_raw)
        except ValueError:
            sandbox = SandboxMode.READ_ONLY

        return cls(
            default_model=os.getenv("CODEX_DEFAULT_MODEL") or None,
            default_timeout=_read_int_env("CODEX_DEFAULT_TIMEOUT", 90),
            default_sandbox=sandbox,
            allowed_dirs=_parse_allowed_dirs(os.getenv("CODEX_ALLOWED_DIRS")),
            max_output_chars=_read_int_env("CODEX_MAX_OUTPUT_CHARS", 12000, minimum=512),
        )


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
