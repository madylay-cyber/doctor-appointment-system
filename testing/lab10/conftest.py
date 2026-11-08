import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# Корректное определение структуры таблиц (DDL)
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fio TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    oms_policy TEXT UNIQUE,
    role_id INTEGER,
    FOREIGN KEY(role_id) REFERENCES Roles(id)
);

CREATE TABLE IF NOT EXISTS Requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    doctor_id INTEGER,
    category_id INTEGER,
    status_id INTEGER,
    datetime_slot TEXT NOT NULL,
    FOREIGN KEY(patient_id) REFERENCES Users(id),
    FOREIGN KEY(doctor_id) REFERENCES Users(id),
    FOREIGN KEY(category_id) REFERENCES Categories(id),
    FOREIGN KEY(status_id) REFERENCES Statuses(id),
    UNIQUE(doctor_id, datetime_slot)
);

CREATE TABLE IF NOT EXISTS Comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    author_id INTEGER,
    text_content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES Requests(id) ON DELETE CASCADE,
    FOREIGN KEY(author_id) REFERENCES Users(id)
);
"""

# Наполнение эталонными тест-кейсами (DML)
SEED_SQL = """
INSERT OR IGNORE INTO Roles (id, role_name) VALUES (1, 'Пациент'), (2, 'Врач'), (3, 'Администратор');

INSERT OR IGNORE INTO Categories (id, category_name) VALUES 
(1, 'Терапия'), (2, 'Кардиология'), (3, 'Неврология'), (4, 'Офтальмология');

INSERT OR IGNORE INTO Statuses (id, status_name) VALUES 
(1, 'Ожидание'), (2, 'Подтверждено'), (3, 'Отменено'), (4, 'Завершен');

INSERT OR IGNORE INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES 
(1, 'Петрова Елена Андреевна', '+79001112233', 'petrova@med.ru', NULL, 2),
(2, 'Иванов Иван Иванович', '+79001112234', 'ivanov@med.ru', NULL, 2),
(3, 'Сидоров Петр Петрович', '+79001112235', 'sidorov@med.ru', NULL, 2),
(4, 'Васильев Сергей Владимирович', '+79001112236', 'vasiliev@med.ru', NULL, 2),
(5, 'Иванова Мария Сергеевна', '+79211234567', 'ivanova@mail.ru', '7824903155670012', 1),
(6, 'Соколов Александр Петрович', '+79319876543', 'sokolov@yandex.ru', '1234567890123456', 1);

INSERT OR IGNORE INTO Requests (id, patient_id, doctor_id, category_id, status_id, datetime_slot) VALUES 
(1, 5, 1, 2, 4, '2026-11-06 09:00'),
(2, 5, 2, 1, 2, '2026-11-06 10:30'),
(3, 6, 1, 2, 2, '2026-11-06 11:00'),
(4, 5, 3, 3, 1, '2026-11-07 14:00'),
(5, 6, 2, 1, 3, '2026-11-07 15:30'),
(6, 5, 1, 2, 2, '2026-11-08 09:00'),
(7, 6, 4, 4, 1, '2026-11-08 10:00'),
(8, 5, 2, 1, 2, '2026-11-08 12:30'),
(9, 6, 3, 3, 4, '2026-11-08 16:00'),
(10, 5, 4, 4, 2, '2026-11-08 17:00'),
(11, 6, 1, 2, 1, '2026-11-08 18:30');
"""

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Фикстура автоматического развертывания чистой тестовой СУБД в памяти перед каждым тестом."""
    settings.db_path = ":memory:"
    
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    # Накатываем структуру таблиц напрямую из строки кодовой базы
    cursor.executescript(SCHEMA_SQL)
    
    # Наполняем базу эталонными сид-данными напрямую из строки кодовой базы
    cursor.executescript(SEED_SQL)
    
    conn.commit()
    conn.close()
    yield
    # База данных стирается из памяти автоматически после окончания теста

@pytest.fixture
def client():
    """Фикстура изолированного виртуального клиента ASGI приложения FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
