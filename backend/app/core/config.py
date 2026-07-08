from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MiGaraje API"
    database_url: str = "sqlite:///./migaraje.db"
    secret_key: str = "dev-secret-solo-para-desarrollo-cambiar-en-produccion"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 días
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
