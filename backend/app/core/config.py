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