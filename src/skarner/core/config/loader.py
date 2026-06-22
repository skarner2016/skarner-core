from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import (
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
)

from .settings import Settings

__all__ = ["load_settings"]

_PROFILE_ENV_VAR = "ENV"
_DEFAULT_ENV = "dev"


def _resolve_env(explicit: str | None) -> str:
    """Pick the active profile: explicit arg > ENV env var > 'dev'."""
    return explicit or os.environ.get(_PROFILE_ENV_VAR, _DEFAULT_ENV)


def _project_root() -> Path | None:
    try:
        return Path(__file__).resolve().parents[3]
    except IndexError:
        return None


def _find_file(name: str, cwd: Path | None) -> Path | None:
    """Search for ``name`` in cwd first, then the project root."""
    roots: list[Path] = [cwd or Path.cwd()]
    root = _project_root()
    if root is not None:
        roots.append(root)
    for base in roots:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def load_settings(
    *,
    env: str | None = None,
    cwd: Path | None = None,
) -> Settings:
    """Load Settings from a layered set of sources.

    Priority (low -> high):
        1. field defaults
        2. ``.env`` (generic dotenv file)
        3. ``.env.{ENV}`` (profile-specific file, overrides ``.env``)
        4. environment variables (highest)

    Args:
        env: Explicit profile name. Falls back to the ``ENV`` environment
            variable, then ``"dev"``.
        cwd: Directory to search for env files. Defaults to the current
            working directory (with the project root as fallback).

    Raises:
        pydantic.ValidationError: A required field is missing or invalid.
    """
    resolved_env = _resolve_env(env)
    generic_file = _find_file(".env", cwd)
    profile_file = _find_file(f".env.{resolved_env}", cwd)

    # Build a per-call subclass so the source chain is captured by closure
    # instead of mutable class state — keeps load_settings reentrant.
    class _BoundSettings(Settings):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[Settings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            # Returned high -> low priority.
            sources: list[PydanticBaseSettingsSource] = [env_settings]
            if profile_file is not None:
                sources.append(
                    DotEnvSettingsSource(
                        settings_cls,
                        env_file=str(profile_file),
                        env_file_encoding="utf-8",
                        case_sensitive=False,
                        env_nested_delimiter="__",
                    )
                )
            if generic_file is not None:
                sources.append(
                    DotEnvSettingsSource(
                        settings_cls,
                        env_file=str(generic_file),
                        env_file_encoding="utf-8",
                        case_sensitive=False,
                        env_nested_delimiter="__",
                    )
                )
            sources.append(init_settings)
            return tuple(sources)

    return _BoundSettings()
