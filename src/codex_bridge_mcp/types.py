from __future__ import annotations

from enum import Enum


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    CODE = "code"


class SandboxMode(str, Enum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"
