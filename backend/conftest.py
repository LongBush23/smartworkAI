import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport

# Override environment variables for testing
os.environ["DB_NAME"] = "smartwork_test"

from backend.main import app
from backend.database import db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Clear test database before starting
    await db.users.delete_many({})
    await db.departments.delete_many({})
    await db.projects.delete_many({})
    await db.tasks.delete_many({})
    await db.performance_logs.delete_many({})
    
    yield
    
    # Cleanup after tests
    await db.users.delete_many({})
    await db.departments.delete_many({})
    await db.projects.delete_many({})
    await db.tasks.delete_many({})
    await db.performance_logs.delete_many({})

@pytest.fixture(scope="function")
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
