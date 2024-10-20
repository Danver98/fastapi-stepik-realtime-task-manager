from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
        # Setup your own .env file with credentials or take them from environmental variables
        env_file = ".env"


settings = Settings()
