import os
from typing import Optional

class Settings:
    def __init__(self):
        self.app_env: str = os.getenv("APP_ENV", "dev")
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/traffic.db")
        self.db_schema: str = os.getenv("DB_SCHEMA", "public")

SETTINGS = Settings()
