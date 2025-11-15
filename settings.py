import os


class Settings:
    """Liest Konfigurationswerte direkt aus den Umgebungsvariablen."""

    @property
    def app_env(self) -> str:
        return os.getenv("APP_ENV", "dev")

    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///data/traffic.db")

    @property
    def db_schema(self) -> str:
        return os.getenv("DB_SCHEMA", "public")


SETTINGS = Settings()
