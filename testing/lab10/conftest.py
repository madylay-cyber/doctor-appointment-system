import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Фикстура автоматического развертывания чистой тестовой СУБД в памяти перед каждым тестом."""
    settings.db_path = ":memory:"
    
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    with open("schema.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    with open("seed.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    conn.commit()
    conn.close()
    yield

@pytest.fixture
def client():
    """Фикстура изолированного виртуального клиента ASGI приложения FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
