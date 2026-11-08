import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Фикстура автоматического развертывания чистой тестовой СУБД в памяти перед каждым тестом."""
    settings.db_path = ":memory:"
    
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    # Определяем абсолютный путь к корню репозитория
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed.sql")
    
    # Накатываем структуру таблиц по абсолютному пути
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    # Наполняем базу эталонными сид-данными
    with open(seed_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    conn.commit()
    conn.close()
    yield
    # База данных стирается из памяти автоматически после окончания теста

@pytest.fixture
def client():
    """Фикстура изолированного виртуального клиента ASGI приложения FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
