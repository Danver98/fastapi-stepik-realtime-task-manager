import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for application"""
    BASE_URL: str
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    USER_PASSWORD_SALT: str
    REFRESH_TOKEN_PASSWORD_SALT: str
    REDIS_URL: str


    @property
    def ASYNC_DATABASE_URL(self):
        """
        Create asynchronous database URL for sqlalchemy engine.

        :return: formatted string with database credentials
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        """Config for application"""
        # Setup your own .env file with credentials or take them from environmental variables
        env_file = ".env"

class DevSettings(Settings):
    """Settings for development environment"""
    class Config:
        """Config for development environment"""
        env_file = ".dev.env"


class TestSettings(Settings):
    """Settings for testing environment"""
    class Config:
        """Config for testing environment"""
        env_file = ".test.env"


class ProdSettings(Settings):
    """Settings for production environment"""
    class Config:
        """Config for production environment"""
        env_file = ".prod.env"


@lru_cache()
def get_settings():
    """Get settings for current environment"""
    app_stage = os.getenv("TASK_MANAGER_APP_STAGE", None)
    if app_stage == "dev":
        return DevSettings()
    if app_stage == "test":
        return TestSettings()
    if app_stage == "prod":
        return ProdSettings()
    return Settings()


settings = get_settings()
