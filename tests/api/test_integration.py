"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.api.main import app
from src.config import settings
from src.db.session import Base


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_engine):
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Knowledge Graph API"}


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_entity_unauthorized(client):
    """Test entity creation requires authentication."""
    entity_data = {
        "name": "Test Entity",
        "type": "test",
        "description": "A test entity"
    }
    response = await client.post("/entities/", json=entity_data)
    assert response.status_code == 403  # Forbidden without auth


@pytest.mark.asyncio
async def test_list_entities_unauthorized(client):
    """Test listing entities requires authentication."""
    response = await client.get("/entities/")
    assert response.status_code == 403  # Forbidden without auth


@pytest.mark.asyncio
async def test_create_user_unauthorized(client):
    """Test user creation requires authentication."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = await client.post("/users/", json=user_data)
    assert response.status_code == 403  # Forbidden without auth


@pytest.mark.asyncio
async def test_sources_endpoint_unauthorized(client):
    """Test sources endpoint requires authentication."""
    response = await client.get("/sources/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_relationships_endpoint_unauthorized(client):
    """Test relationships endpoint requires authentication."""
    response = await client.get("/relationships/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_endpoint_unauthorized(client):
    """Test audit endpoint requires authentication."""
    response = await client.get("/audit/")
    assert response.status_code == 403
