"""
Pytest configuration and shared fixtures for backend tests.
"""
import asyncio
import os
from typing import Generator, AsyncGenerator
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pytest_asyncio

# Add backend to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app
from backend.database import Base, get_db
from backend.config import settings
from backend.core.container import get_container


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def test_app(test_db):
    """Create test FastAPI application."""
    # Override database dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Reset container for testing
    container = get_container()
    container.reset()
    container.initialize()
    
    yield app
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app) -> TestClient:
    """Create synchronous test client."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="function")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def mock_settings(monkeypatch):
    """Mock application settings."""
    def _mock_settings(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setattr(settings, key, value)
    return _mock_settings


@pytest.fixture
def test_marker_data():
    """Sample marker data for testing."""
    return {
        "name": "TEST_MARKER",
        "category": "test",
        "confidence": 0.95,
        "description": "Test marker for unit tests",
        "metadata": {
            "source": "test",
            "version": "1.0"
        }
    }


@pytest.fixture
def test_analysis_request():
    """Sample analysis request for testing."""
    return {
        "text": "This is a test text for marker analysis.",
        "language": "de",
        "options": {
            "include_metadata": True,
            "confidence_threshold": 0.7
        }
    }


@pytest.fixture
def mock_response_time(monkeypatch):
    """Mock response time tracking."""
    import time
    
    class MockTime:
        def __init__(self):
            self.current = 0
        
        def time(self):
            self.current += 0.1
            return self.current
    
    mock_time = MockTime()
    monkeypatch.setattr(time, "time", mock_time.time)
    return mock_time


# Async fixtures for service testing
@pytest_asyncio.fixture
async def mock_marker_repository():
    """Mock marker repository for unit tests."""
    from unittest.mock import AsyncMock, Mock
    
    repository = Mock()
    repository.create = AsyncMock()
    repository.get = AsyncMock()
    repository.get_all = AsyncMock()
    repository.update = AsyncMock()
    repository.delete = AsyncMock()
    
    return repository


@pytest_asyncio.fixture
async def mock_analysis_service():
    """Mock analysis service for unit tests."""
    from unittest.mock import AsyncMock, Mock
    
    service = Mock()
    service.analyze_text = AsyncMock()
    service.get_markers = AsyncMock()
    service.calculate_confidence = AsyncMock()
    
    return service


# Performance testing fixtures
@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
        
        def start(self, name: str):
            self.metrics[name] = {"start": time.time()}
        
        def end(self, name: str):
            if name in self.metrics:
                self.metrics[name]["end"] = time.time()
                self.metrics[name]["duration"] = (
                    self.metrics[name]["end"] - self.metrics[name]["start"]
                )
        
        def get_duration(self, name: str) -> float:
            return self.metrics.get(name, {}).get("duration", 0)
    
    return PerformanceTracker()


# Test data factories
@pytest.fixture
def marker_factory():
    """Factory for creating test markers."""
    def _create_marker(**kwargs):
        defaults = {
            "id": 1,
            "name": "TEST_MARKER",
            "category": "test",
            "confidence": 0.9,
            "description": "Test marker",
            "metadata": {}
        }
        defaults.update(kwargs)
        return defaults
    return _create_marker


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


# Test utilities
@pytest.fixture
def assert_response():
    """Helper for asserting API responses."""
    def _assert_response(response, status_code=200, contains=None, not_contains=None):
        assert response.status_code == status_code
        
        if contains:
            response_data = response.json()
            for key in contains:
                assert key in response_data
        
        if not_contains:
            response_data = response.json()
            for key in not_contains:
                assert key not in response_data
    
    return _assert_response