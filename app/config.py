from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str
    algorithm: str
    secret_key: str
    access_token_expire_minutes: int
    debug: bool = False
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str
    aws_bucket_name: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
