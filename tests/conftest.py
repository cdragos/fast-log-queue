import pytest
from httpx import AsyncClient


@pytest.fixture(scope="session")
def anyio_backend():
    """Specify the backend to be used by anyio."""
    return "asyncio"


@pytest.fixture
def async_app():
    from api.main import app

    return app


@pytest.fixture
async def async_client(async_app):
    """Creates a new instance of an async client for the application."""
    async with AsyncClient(app=async_app, base_url="http://test") as async_client:
        yield async_client
