from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    APP_VERSION: str
    MONGO_DB_URI: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str

    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: str
    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_PUBLIC_KEY_URL: str

    ENCRYPTION_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

CONFIG = Config()