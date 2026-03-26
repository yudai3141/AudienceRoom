import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "local")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "audienceroom")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "app")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "app")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "demo-audienceroom")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # VOICEVOX Settings
    VOICEVOX_HOST: str = os.getenv("VOICEVOX_HOST", "voicevox")
    VOICEVOX_PORT: int = int(os.getenv("VOICEVOX_PORT", "50021"))

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "test"


settings = Settings()