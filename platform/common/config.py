import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    A Pydantic BaseSettings class for loading environment variables.
    """
    app_name: str = "Sophia AI Platform"
    admin_email: str
    items_per_user: int = 50

    class Config:
        env_file = ".env"

settings = Settings()