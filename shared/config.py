from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str = "fastlogqueue"
    POSTGRES_PASSWORD: str = "mysecretpassword"
    POSTGRES_PORT: str = "5434"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"

    QUEUE_URL: str = ""
    SQLALCHEMY_ASYNC_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_ASYNC_DATABASE_URI", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v

        return (
            f"postgresql+asyncpg://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_SERVER}/{cls.POSTGRES_DB}"
        )


settings = Settings()
