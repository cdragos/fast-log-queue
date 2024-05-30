from typing import AsyncGenerator

from fastapi import Request

from shared.models.session import AsyncSessionLocal


async def get_async_db(request: Request = None) -> AsyncGenerator:  # pyright: ignore
    """Async version of get_db"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()
