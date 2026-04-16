from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    APP_VERSION: str
    MONGO_DB_URI: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

CONFIG = Config()