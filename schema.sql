-- Включаем поддержку внешних ключей в SQLite
PRAGMA foreign_keys = ON;

-- 1. Таблица Ролей
CREATE TABLE Roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

-- 2. Таблица Пользователей
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fio TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    oms_policy TEXT UNIQUE, -- Уникальный полис ОМС (для пациентов)
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(id) ON DELETE RESTRICT
);

-- 3. Таблица Категорий / Специализаций (МКБ-10)
CREATE TABLE Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    icd_code TEXT NOT NULL UNIQUE -- Код МКБ-10
);

-- 4. Таблица Статусов
CREATE TABLE Statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status_name TEXT NOT NULL UNIQUE
);

-- 5. Таблица Заявок (Приемов)
CREATE TABLE Requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    datetime_slot TEXT NOT NULL, -- Формат: YYYY-MM-DD HH:MM
    FOREIGN KEY (patient_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Users(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (status_id) REFERENCES Statuses(id) ON DELETE RESTRICT,
    -- Защита от Race Condition (нельзя записать разных пациентов к одному врачу на одно время)
    UNIQUE(doctor_id, datetime_slot) 
);

-- 6. Таблица Комментариев / Заключений
CREATE TABLE Comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    created_at TEXT NOT NULL, -- Формат: YYYY-MM-DD HH:MM:SS
    FOREIGN KEY (request_id) REFERENCES Requests(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES Users(id) ON DELETE CASCADE
);
