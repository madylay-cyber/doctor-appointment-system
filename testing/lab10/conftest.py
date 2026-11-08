import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

def find_file_in_project(filename):
    """Рекурсивный поиск файла от корня текущей рабочей директории."""
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Критическая ошибка: файл {filename} не найден в структуре проекта!")

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Фикстура автоматического развертывания чистой тестовой СУБД в памяти перед каждым тестом."""
    settings.db_path = ":memory:"
    
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    # Автоматически находим точные пути к скриптам миграций
    schema_path = find_file_in_project("schema.sql")
    seed_path = find_file_in_project("seed.sql")
    
    # Накатываем структуру таблиц
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
