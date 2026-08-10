from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRETS_DIR = Path(__file__).resolve().parents[2] / ".secrets"
GITHUB_TOKEN_FILE = SECRETS_DIR / "github_token"


def _read_token_file() -> str:
    try:
        return GITHUB_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+asyncmy://skill_finder:change_me@127.0.0.1:3306/skill_finder?charset=utf8mb4"
    github_token: SecretStr = SecretStr("")
    admin_key: SecretStr = SecretStr("")
    business_timezone: str = "Asia/Shanghai"
    collection_cron: str = "0 2 * * *"
    scheduler_enabled: bool = False
    min_stars: int = 100
    cors_origins: str = "http://localhost:5173"
    intro_enabled: bool = False
    intro_model: str = "opencode-go/deepseek-v4-flash"
    intro_batch_size: int = 5
    intro_timeout_seconds: int = 300

    @model_validator(mode="after")
    def _load_token_from_file(self) -> Settings:
        if not self.github_token.get_secret_value():
            self.github_token = SecretStr(_read_token_file())
        return self


settings = Settings()
