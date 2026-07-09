from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    algorithm: str
    secret_key: str
    access_token_expire_minutes: str
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
