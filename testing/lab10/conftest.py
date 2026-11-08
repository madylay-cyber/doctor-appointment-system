import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(autouse=True, scope="function")
def enforce_production_db_path():
    """Фикстура гарантирует, что тесты обращаются к файлу medical.db."""
    settings.db_path = "medical.db"
    yield

@pytest.fixture
def client():
    """Фикстура изолированного виртуального клиента ASGI приложения FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
