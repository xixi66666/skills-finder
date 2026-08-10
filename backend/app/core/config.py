from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
