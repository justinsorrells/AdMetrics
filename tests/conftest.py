"""Shared test fixtures."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admetrics.api.main import create_app
from admetrics.config import Settings


@pytest.fixture
def app(tmp_path) -> Iterator:
    """Create an isolated application instance per test."""

    settings = Settings(
        app_name="AdMetrics Test API",
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    application = create_app(settings)
    yield application
    application.state.db.dispose()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    """Provide an async HTTP client for the FastAPI app."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
