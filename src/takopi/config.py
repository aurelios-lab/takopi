from __future__ import annotations

import os
import tomllib
from pathlib import Path

# Environment variable names for secrets
ENV_BOT_TOKEN = "TAKOPI_BOT_TOKEN"
ENV_CHAT_ID = "TAKOPI_CHAT_ID"

LOCAL_CONFIG_NAME = Path(".takopi") / "takopi.toml"
LOCAL_CONFIG_SIMPLE = Path("takopi.toml")  # Also support takopi.toml in cwd
HOME_CONFIG_PATH = Path.home() / ".takopi" / "takopi.toml"
LEGACY_LOCAL_CONFIG_NAME = Path(".codex") / "takopi.toml"
LEGACY_HOME_CONFIG_PATH = Path.home() / ".codex" / "takopi.toml"


class ConfigError(RuntimeError):
    pass


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Override values take precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _local_config_candidates() -> list[Path]:
    """Return local config candidates (cwd-based), in priority order."""
    cwd = Path.cwd()
    return [
        cwd / LOCAL_CONFIG_SIMPLE,      # ./takopi.toml
        cwd / LOCAL_CONFIG_NAME,         # ./.takopi/takopi.toml
    ]


def _try_read_config(cfg_path: Path) -> dict | None:
    """Try to read config, return None if not found."""
    if not cfg_path.is_file():
        return None
    try:
        raw = cfg_path.read_text(encoding="utf-8")
        return tomllib.loads(raw)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _config_candidates() -> list[Path]:
    candidates = [Path.cwd() / LOCAL_CONFIG_NAME, HOME_CONFIG_PATH]
    if candidates[0] == candidates[1]:
        return [candidates[0]]
    return candidates


def _legacy_candidates() -> list[Path]:
    candidates = [Path.cwd() / LEGACY_LOCAL_CONFIG_NAME, LEGACY_HOME_CONFIG_PATH]
    if candidates[0] == candidates[1]:
        return [candidates[0]]
    return candidates


def _maybe_migrate_legacy(legacy_path: Path, target_path: Path) -> None:
    if target_path.exists():
        if not target_path.is_file():
            raise ConfigError(
                f"Config path {target_path} exists but is not a file."
            ) from None
        return
    if not legacy_path.is_file():
        return
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        raw = legacy_path.read_text(encoding="utf-8")
        target_path.write_text(raw, encoding="utf-8")
    except OSError as e:
        raise ConfigError(
            f"Failed to migrate legacy config {legacy_path} to {target_path}: {e}"
        ) from e


def _read_config(cfg_path: Path) -> dict:
    try:
        raw = cfg_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(f"Missing config file {cfg_path}.") from None
    except OSError as e:
        raise ConfigError(f"Failed to read config file {cfg_path}: {e}") from e
    try:
        return tomllib.loads(raw)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Malformed TOML in {cfg_path}: {e}") from None


def load_telegram_config(path: str | Path | None = None) -> tuple[dict, Path]:
    if path:
        cfg_path = Path(path).expanduser()
        return _read_config(cfg_path), cfg_path

    # Migrate legacy configs if needed
    for legacy, target in zip(_legacy_candidates(), _config_candidates(), strict=True):
        _maybe_migrate_legacy(legacy, target)

    # Load global config (required)
    global_config: dict | None = None
    global_path: Path | None = None

    if HOME_CONFIG_PATH.is_file():
        global_config = _try_read_config(HOME_CONFIG_PATH)
        global_path = HOME_CONFIG_PATH
    elif LEGACY_HOME_CONFIG_PATH.is_file():
        global_config = _try_read_config(LEGACY_HOME_CONFIG_PATH)
        global_path = LEGACY_HOME_CONFIG_PATH

    if global_config is None:
        raise ConfigError("Missing takopi config at ~/.takopi/takopi.toml")

    # Check for local config override (optional)
    for local_candidate in _local_config_candidates():
        local_config = _try_read_config(local_candidate)
        if local_config is not None:
            # Merge: local overrides global
            merged = _deep_merge(global_config, local_config)
            return merged, local_candidate

    # No local config, use global only
    return global_config, global_path


def get_bot_token(config: dict, config_path: Path) -> str:
    """Get bot token from environment variable or config file.

    Environment variable TAKOPI_BOT_TOKEN takes precedence over config file.
    """
    # Check environment variable first
    env_token = os.environ.get(ENV_BOT_TOKEN)
    if env_token and env_token.strip():
        return env_token.strip()

    # Fall back to config file
    try:
        token = config["bot_token"]
    except KeyError:
        raise ConfigError(
            f"Missing bot token. Set {ENV_BOT_TOKEN} environment variable "
            f"or add `bot_token` to {config_path}."
        ) from None

    if not isinstance(token, str) or not token.strip():
        raise ConfigError(
            f"Invalid `bot_token` in {config_path}; expected a non-empty string."
        )
    return token.strip()


def get_chat_id(config: dict, config_path: Path) -> int:
    """Get chat ID from environment variable or config file.

    Environment variable TAKOPI_CHAT_ID takes precedence over config file.
    """
    # Check environment variable first
    env_chat_id = os.environ.get(ENV_CHAT_ID)
    if env_chat_id and env_chat_id.strip():
        try:
            return int(env_chat_id.strip())
        except ValueError:
            raise ConfigError(
                f"Invalid {ENV_CHAT_ID} environment variable; expected an integer."
            ) from None

    # Fall back to config file
    try:
        chat_id_value = config["chat_id"]
    except KeyError:
        raise ConfigError(
            f"Missing chat ID. Set {ENV_CHAT_ID} environment variable "
            f"or add `chat_id` to {config_path}."
        ) from None

    if isinstance(chat_id_value, bool) or not isinstance(chat_id_value, int):
        raise ConfigError(
            f"Invalid `chat_id` in {config_path}; expected an integer."
        )
    return chat_id_value
