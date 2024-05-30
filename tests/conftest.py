import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from shared.config import settings
from shared.models.base_class import Base


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


@pytest.fixture(scope="session")
def test_postgres():
    """Starts and stops the Postgres test container."""
    test_postgres = PostgresContainer("postgres:9.5")
    test_postgres.start()
    yield test_postgres
    test_postgres.stop()


@pytest.fixture
async def async_db(test_postgres, monkeypatch):
    """
    Asynchronously establishes a connection with the test database, creates tables,
    yields the session and rolls back any changes.
    """
    test_postgres.driver = "+asyncpg"
    postgres_async_url = test_postgres.get_connection_url()

    monkeypatch.setattr(settings, "SQLALCHEMY_ASYNC_DATABASE_URI", postgres_async_url)

    async_engine = create_async_engine(postgres_async_url)
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        async with async_session(bind=connection) as session:
            yield session
            await session.flush()
            await session.rollback()
