import pytest
from pydantic import ValidationError

from skarner.core.config import Settings, load_settings
from skarner.core.db.engine import DatabaseConfig, DatabaseDialect


# Environment variables that could leak into Settings and break isolation.
_LEAKY_VARS = [
    "ENV",
    "APP_NAME",
    "DEBUG",
    "LOG_LEVEL",
    "JWT__SECRET",
    "JWT__ALGORITHM",
    "DB__HOST",
    "DB__DIALECT",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Strip any ambient config env vars so tests are deterministic."""
    for var in _LEAKY_VARS:
        monkeypatch.delenv(var, raising=False)
    yield


def _write(path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


# --- defaults ---

def test_defaults_when_only_required_given(tmp_path, monkeypatch):
    _write(tmp_path / ".env", "JWT__SECRET=top-secret")
    settings = load_settings(cwd=tmp_path)

    assert settings.app_name == "skarner"
    assert settings.env == "dev"
    assert settings.log_level == "INFO"
    assert settings.debug is False
    assert settings.jwt.secret.get_secret_value() == "top-secret"
    assert settings.jwt.algorithm == "HS256"


# --- .env loading ---

def test_dotenv_overrides_defaults(tmp_path):
    _write(
        tmp_path / ".env",
        """
        APP_NAME=billing
        LOG_LEVEL=DEBUG
        JWT__SECRET=s1
        """,
    )
    settings = load_settings(cwd=tmp_path)

    assert settings.app_name == "billing"
    assert settings.log_level == "DEBUG"


# --- profile priority ---

def test_profile_file_overrides_dotenv(tmp_path):
    _write(tmp_path / ".env", "APP_NAME=generic\nLOG_LEVEL=INFO\nJWT__SECRET=s")
    _write(tmp_path / ".env.prod", "LOG_LEVEL=WARNING")

    settings = load_settings(env="prod", cwd=tmp_path)

    # profile file wins over .env
    assert settings.log_level == "WARNING"
    # value only present in .env is still inherited
    assert settings.app_name == "generic"


def test_env_var_selects_profile(tmp_path, monkeypatch):
    _write(tmp_path / ".env", "JWT__SECRET=s\nLOG_LEVEL=INFO")
    _write(tmp_path / ".env.prod", "LOG_LEVEL=ERROR")
    monkeypatch.setenv("ENV", "prod")

    settings = load_settings(cwd=tmp_path)

    assert settings.log_level == "ERROR"


# --- env var highest priority ---

def test_env_var_overrides_everything(tmp_path, monkeypatch):
    _write(tmp_path / ".env", "LOG_LEVEL=INFO\nJWT__SECRET=s")
    _write(tmp_path / ".env.prod", "LOG_LEVEL=WARNING")
    monkeypatch.setenv("LOG_LEVEL", "CRITICAL")

    settings = load_settings(env="prod", cwd=tmp_path)

    assert settings.log_level == "CRITICAL"


# --- nested config ---

def test_nested_db_from_dotenv(tmp_path):
    _write(
        tmp_path / ".env",
        """
        JWT__SECRET=s
        DB__DIALECT=mysql
        DB__HOST=db.internal
        DB__PORT=3307
        DB__USER=root
        DB__PASSWORD=pw
        DB__DATABASE=app
        """,
    )
    settings = load_settings(cwd=tmp_path)

    assert settings.db is not None
    assert settings.db.dialect == DatabaseDialect.MYSQL
    assert settings.db.host == "db.internal"
    assert settings.db.port == 3307


def test_nested_db_from_env_var(tmp_path, monkeypatch):
    _write(
        tmp_path / ".env",
        """
        JWT__SECRET=s
        DB__DIALECT=mysql
        DB__HOST=db.internal
        DB__USER=root
        DB__PASSWORD=pw
        DB__DATABASE=app
        """,
    )
    monkeypatch.setenv("DB__HOST", "override.host")

    settings = load_settings(cwd=tmp_path)

    assert settings.db.host == "override.host"


# --- bridge to DatabaseConfig ---

def test_to_database_config_bridge(tmp_path):
    _write(
        tmp_path / ".env",
        """
        JWT__SECRET=s
        DB__DIALECT=postgresql
        DB__HOST=pg
        DB__PORT=5432
        DB__USER=admin
        DB__PASSWORD=pass
        DB__DATABASE=pgdb
        DB__POOL_SIZE=5
        """,
    )
    settings = load_settings(cwd=tmp_path)
    cfg = settings.db.to_database_config()

    assert isinstance(cfg, DatabaseConfig)
    assert cfg.dialect == DatabaseDialect.POSTGRESQL
    assert cfg.pool_size == 5
    assert cfg.build_url() == "postgresql+asyncpg://admin:pass@pg:5432/pgdb"


# --- validation ---

def test_missing_required_jwt_secret_raises(tmp_path):
    _write(tmp_path / ".env", "APP_NAME=x")
    with pytest.raises(ValidationError):
        load_settings(cwd=tmp_path)


def test_secret_not_leaked_in_repr(tmp_path):
    _write(tmp_path / ".env", "JWT__SECRET=super-secret-value")
    settings = load_settings(cwd=tmp_path)

    assert "super-secret-value" not in repr(settings)


# --- direct construction still works ---

def test_direct_construction(monkeypatch):
    for var in _LEAKY_VARS:
        monkeypatch.delenv(var, raising=False)
    settings = Settings(jwt={"secret": "abc"})
    assert settings.jwt.secret.get_secret_value() == "abc"
    assert settings.env == "dev"
