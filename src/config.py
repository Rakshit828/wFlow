from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    APP_VERSION: str
    ENVIRONMENT: str
    MONGO_DB_URI: str
    DATABASE_NAME: str 

    GROQ_API_KEY: str
    GEMINI_API_KEY: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_LOGIN_REDIRECT_URL: str
    GOOGLE_SCOPE_REDIRECT_URL: str
    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_PUBLIC_KEY_URL: str

    ENCRYPTION_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRY: str
    REFRESH_TOKEN_EXPIRY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

CONFIG = Config()