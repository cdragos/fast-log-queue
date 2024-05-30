from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str = "fastlogqueue"
    POSTGRES_PASSWORD: str = "mysecretpassword"
    POSTGRES_PORT: str = "5432"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"

    QUEUE_URL: str = ""
    SQLALCHEMY_ASYNC_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_ASYNC_DATABASE_URI", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if v and isinstance(v, str):
            return v

        return f"postgresql+asyncpg://{info.data['POSTGRES_USER']}:{info.data['POSTGRES_PASSWORD']}@{info.data['POSTGRES_SERVER']}/{info.data['POSTGRES_DB']}"


settings = Settings()
