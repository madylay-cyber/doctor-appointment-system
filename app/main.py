import sqlite3
import os
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.users.router import router as users_router
from app.appointments.router import router as appointments_router
from app.core.health import router as health_router

app = FastAPI(title="Medical Appointment & Booking System API", version="2.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def init_db():
    print("⏳ Проверка базы данных...")
    conn = sqlite3.connect("medical.db", timeout=20)
    cursor = conn.cursor()
    
    # 1. СОЗДАЕМ ТАБЛИЦЫ, ЕСЛИ ИХ НЕТ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            oms_policy TEXT UNIQUE,
            role_id INTEGER NOT NULL
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS Categories (id INTEGER PRIMARY KEY, name TEXT, icd_code TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Statuses (id INTEGER PRIMARY KEY, status_name TEXT)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            category_id INTEGER,
            status_id INTEGER,
            datetime_slot TEXT
        )
    """)
    
    # 2. ОЧИЩАЕМ КОНФЛИКТЫ (чтобы база не падала с ошибкой UNIQUE)
    # Если у кого-то другого есть эти полисы - мы их стираем, чтобы отдать Админу и Ивановой
    cursor.execute("UPDATE Users SET oms_policy = NULL WHERE oms_policy = '0000000000000000' AND id != 3")
    cursor.execute("UPDATE Users SET oms_policy = NULL WHERE oms_policy = '7824903155670012' AND id != 6")

    # 3. ЖЕСТКО ФИКСИРУЕМ АДМИНИСТРАТОРА (ID 3)
    cursor.execute("SELECT id FROM Users WHERE id = 3")
    if cursor.fetchone():
        cursor.execute("UPDATE Users SET email = 'smirnova@clinic.ru', role_id = 3, oms_policy = '0000000000000000' WHERE id = 3")
        print("✅ Данные Администратора обновлены.")
    else:
        cursor.execute("INSERT INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (3, 'Смирнова Анна Викторовна', '+79990000000', 'smirnova@clinic.ru', '0000000000000000', 3)")
        print("✅ Администратор создан.")

    # 4. ЖЕСТКО ФИКСИРУЕМ ПАЦИЕНТА ИВАНОВУ (ID 6)
    cursor.execute("SELECT id FROM Users WHERE id = 6")
    if cursor.fetchone():
        cursor.execute("UPDATE Users SET oms_policy = '7824903155670012', fio = 'Иванова Мария Сергеевна', role_id = 1 WHERE id = 6")
    else:
        cursor.execute("INSERT INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (6, 'Иванова Мария Сергеевна', '+79214567890', 'ivanova@mail.ru', '7824903155670012', 1)")

    # 5. ДОБАВЛЯЕМ ВРАЧЕЙ (если их нет)
    doctors = [
        (2, "Петрова Елена Андреевна", "+79991112233", "petrova@clinic.ru"),
        (4, "Ким Алексей Борисович", "+79992223344", "kim@clinic.ru"),
        (5, "Васильев Игорь Олегович", "+79993334455", "vasiliev@clinic.ru")
    ]
    for doc_id, fio, phone, email in doctors:
        cursor.execute("INSERT OR IGNORE INTO Users (id, fio, phone, email, role_id) VALUES (?, ?, ?, ?, 2)", (doc_id, fio, phone, email))

    # 6. КАТЕГОРИИ И СТАТУСЫ
    cursor.execute("INSERT OR IGNORE INTO Categories (id, name, icd_code) VALUES (1, 'Терапия', 'A00')")
    cursor.execute("INSERT OR IGNORE INTO Categories (id, name, icd_code) VALUES (4, 'Кардиология', 'I10')")
    cursor.execute("INSERT OR IGNORE INTO Statuses (id, status_name) VALUES (1, 'Инициация')")
    cursor.execute("INSERT OR IGNORE INTO Statuses (id, status_name) VALUES (2, 'Подтверждено')")
            
    conn.commit()
    conn.close()
    print("✅ База данных готова к работе.")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    details = [{"field": err["loc"][-1], "issue": str(err["msg"])} for err in errors]
    return JSONResponse(status_code=422, content={"status": "error", "message": "Ошибка валидации", "details": details})

@app.exception_handler(sqlite3.IntegrityError)
async def sqlite_integrity_handler(request: Request, exc: sqlite3.IntegrityError):
    return JSONResponse(status_code=400, content={"status": "error", "message": "Нарушение целостности данных СУБД."})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": str(exc.detail)})

app.include_router(health_router)
app.include_router(users_router)
app.include_router(appointments_router)

if __name__ == "__main__":
    import uvicorn
    cloud_port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=cloud_port)
