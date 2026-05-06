from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart School FastAPI"
    api_prefix: str = "/api"
    secret_key: str  # Must be set via .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    sqlserver_connection_string: str = "sqlite:///./school.db"

    # Email Settings
    mail_username: str = "admin@school.com"
    mail_password: str = "password"
    mail_from: str = "admin@school.com"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "Smart School"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = True
    validate_certs: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
