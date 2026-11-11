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
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    # Создаем таблицу Users, если её нет
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
    
    # ПРИНУДИТЕЛЬНО ДОБАВЛЯЕМ КОЛОНКИ, ЕСЛИ БАЗА БЫЛА СОЗДАНА РАНЬШЕ
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN phone TEXT")
        print("✅ Колонка phone добавлена.")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN email TEXT")
        print("✅ Колонка email добавлена.")
    except sqlite3.OperationalError:
        pass
        
    # Добавляем админа
    cursor.execute("SELECT id FROM Users WHERE email = 'smirnova@clinic.ru'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO Users (fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, 3)",
            ("Смирнова Анна Викторовна", "+79990000000", "smirnova@clinic.ru", "7824903155670012")
        )
        print("✅ Администратор добавлен.")
    
    # Добавляем врачей
    doctors = [
        ("Петрова Елена Андреевна", "+79991112233", "petrova@clinic.ru"),
        ("Ким Алексей Борисович", "+79992223344", "kim@clinic.ru"),
        ("Васильев Игорь Олегович", "+79993334455", "vasiliev@clinic.ru")
    ]
    for fio, phone, email in doctors:
        cursor.execute("SELECT id FROM Users WHERE fio = ? AND role_id = 2", (fio,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO Users (fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, NULL, 2)",
                (fio, phone, email)
            )
            
    conn.commit()
    conn.close()
    print("✅ Проверка завершена.")

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
