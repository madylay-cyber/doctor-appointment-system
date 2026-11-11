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
    # timeout=20 спасает от ошибки database is locked
    conn = sqlite3.connect("medical.db", timeout=20)
    cursor = conn.cursor()
    
    # 1. СОЗДАЕМ ВСЕ НЕОБХОДИМЫЕ ТАБЛИЦЫ
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
    
    # ВОТ ЭТОЙ ТАБЛИЦЫ НЕ ХВАТАЛО
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            category_id INTEGER,
            status_id INTEGER,
            datetime_slot TEXT,
            FOREIGN KEY (patient_id) REFERENCES Users(id),
            FOREIGN KEY (doctor_id) REFERENCES Users(id),
            FOREIGN KEY (category_id) REFERENCES Categories(id),
            FOREIGN KEY (status_id) REFERENCES Statuses(id)
        )
    """)
    
    # 2. ДОБАВЛЯЕМ ПАЦИЕНТА ИВАНОВУ (ID 6, ПОЛИС НУЖНЫЙ ДЛЯ ТЕСТА)
    cursor.execute(
        "INSERT OR IGNORE INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, ?, 1)",
        (6, "Иванова Мария Сергеевна", "+79214567890", "ivanova@mail.ru", "7824903155670012")
    )
    
    # 3. ДОБАВЛЯЕМ АДМИНИСТРАТОРА СМИРНОВУ (ID 3, С ДРУГИМ ПОЛИСОМ)
    cursor.execute(
        "INSERT OR IGNORE INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, ?, 3)",
        (3, "Смирнова Анна Викторовна", "+79990000000", "smirnova@clinic.ru", "0000000000000000")
    )
    
    # 4. ДОБАВЛЯЕМ ВРАЧЕЙ
    doctors = [
        (2, "Петрова Елена Андреевна", "+79991112233", "petrova@clinic.ru"),
        (4, "Ким Алексей Борисович", "+79992223344", "kim@clinic.ru"),
        (5, "Васильев Игорь Олегович", "+79993334455", "vasiliev@clinic.ru")
    ]
    for doc_id, fio, phone, email in doctors:
        cursor.execute("INSERT OR IGNORE INTO Users (id, fio, phone, email, role_id) VALUES (?, ?, ?, ?, 2)", (doc_id, fio, phone, email))

    # 5. ДОБАВЛЯЕМ КАТЕГОРИИ И СТАТУСЫ
    cursor.execute("INSERT OR IGNORE INTO Categories (id, name, icd_code) VALUES (1, 'Терапия', 'A00')")
    cursor.execute("INSERT OR IGNORE INTO Categories (id, name, icd_code) VALUES (4, 'Кардиология', 'I10')")
    cursor.execute("INSERT OR IGNORE INTO Statuses (id, status_name) VALUES (1, 'Инициация')")
    cursor.execute("INSERT OR IGNORE INTO Statuses (id, status_name) VALUES (2, 'Подтверждено')")
            
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована.")

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
