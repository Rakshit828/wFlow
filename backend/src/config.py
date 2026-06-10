from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    APP_VERSION: str
    ENVIRONMENT: str

    POSTGRES_DB_URL: str
    TEMPORAL_URL: str

    FRONTEND_URL: str
    BACKEND_URL: str

    GROQ_API_KEY: str
    GEMINI_API_KEY: str

    BASE_LOGIN_REDIRECT_URL: str
    BASE_SCOPE_REDIRECT_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_PUBLIC_KEY_URL: str
    GOOGLE_PUBSUB_TOPIC: str

    GITHUB_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_AUTH_URL: str
    GITHUB_TOKEN_URL: str
    GITHUB_GET_PROFILE_URL: str

    SESSION_TOKEN_EXPIRY: str

    ENCRYPTION_KEY: str
    LOCAL_STORAGE_PATH: str

    @property
    def GOOGLE_LOGIN_REDIRECT_URL(self) -> str:
        return self.BACKEND_URL + self.BASE_LOGIN_REDIRECT_URL.format(provider="google")

    @property
    def GOOGLE_SCOPE_REDIRECT_URL(self) -> str:
        return self.BACKEND_URL + self.BASE_SCOPE_REDIRECT_URL.format(provider="google")

    @property
    def GITHUB_LOGIN_REDIRECT_URL(self) -> str:
        return self.BASE_LOGIN_REDIRECT_URL.format(provider="github")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


CONFIG = Config()
