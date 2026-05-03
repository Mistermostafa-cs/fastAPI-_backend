from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart School FastAPI"
    api_prefix: str = "/api"
    secret_key: str  # Must be set via .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    sqlserver_connection_string: str = "sqlite:///./school.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
