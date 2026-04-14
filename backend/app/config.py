from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILES = [
    PROJECT_ROOT / ".env.local",
    PROJECT_ROOT / ".env",
]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


for env_file in ENV_FILES:
    _load_env_file(env_file)


NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY") or os.getenv("NGC_API_KEY") or ""
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
NVIDIA_TIMEOUT = float(os.getenv("NVIDIA_TIMEOUT", "25"))
NVIDIA_MAX_TOKENS = int(os.getenv("NVIDIA_MAX_TOKENS", "512"))
NVIDIA_USE_REMOTE = os.getenv("NVIDIA_USE_REMOTE", "1").lower() not in {"0", "false", "no", "off"}

