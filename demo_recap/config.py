from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "demo_recaps.sqlite"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    groq_api_key: str
    groq_model: str

    @property
    def has_groq_api_key(self) -> bool:
        return bool(self.groq_api_key.strip())


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a small repo-local .env file without mutating process env."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _config_value(env_file_values: dict[str, str], key: str, default: str = "") -> str:
    env_file_value = env_file_values.get(key)
    if env_file_value:
        return env_file_value
    return os.environ.get(key, default)


def _resolve_db_path(raw_path: str) -> Path:
    if not raw_path.strip():
        return DEFAULT_DB_PATH
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_config() -> AppConfig:
    env_file_values = _parse_env_file(REPO_ROOT / ".env")
    return AppConfig(
        db_path=_resolve_db_path(_config_value(env_file_values, "DEMO_RECAP_DB_PATH")),
        groq_api_key=_config_value(env_file_values, "GROQ_API_KEY"),
        groq_model=_config_value(env_file_values, "GROQ_MODEL", DEFAULT_GROQ_MODEL),
    )
