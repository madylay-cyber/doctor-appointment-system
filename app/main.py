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
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
        
    # 1. ДОБАВЛЯЕМ ИЛИ ОБНОВЛЯЕМ АДМИНИСТРАТОРА (Безопасная проверка)
    # Ищем, есть ли уже кто-то с таким ОМС или Email
    cursor.execute("SELECT id FROM Users WHERE oms_policy = '7824903155670012' OR email = 'smirnova@clinic.ru'")
    admin_row = cursor.fetchone()
    
    if admin_row:
        # Если такой пользователь уже есть, принудительно делаем его Админом и обновляем данные
        cursor.execute(
            "UPDATE Users SET fio = 'Смирнова Анна Викторовна', role_id = 3, email = 'smirnova@clinic.ru', phone = '+79990000000' WHERE id = ?",
            (admin_row[0],)
        )
        print("✅ Данные администратора обновлены (Email добавлен).")
    else:
        # Если никого не нашли - создаем нового админа
        cursor.execute(
            "INSERT INTO Users (fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, 3)",
            ("Смирнова Анна Викторовна", "+79990000000", "smirnova@clinic.ru", "7824903155670012")
        )
        print("✅ Администратор создан.")
    
    # 2. ДОБАВЛЯЕМ ВРАЧЕЙ
    doctors = [
        ("Петрова Елена Андреевна", "+79991112233", "petrova@clinic.ru"),
        ("Ким Алексей Борисович", "+79992223344", "kim@clinic.ru"),
        ("Васильев Игорь Олегович", "+79993334455", "vasiliev@clinic.ru"),
        ("Смирнов Иван Петрович", "+79994445566", "smirnov@clinic.ru"),
        ("Иванова Анна Сергеевна", "+79995556677", "ivanova@clinic.ru"),
        ("Морозов Олег Дмитриевич", "+79996667788", "morozov@clinic.ru"),
        ("Соколова Екатерина Игоревна", "+79997778899", "sokolova@clinic.ru"),
        ("Лебедев Дмитрий Николаевич", "+79998889900", "lebedev@clinic.ru"),
        ("Козлов Сергей Владимирович", "+79999990011", "kozlov@clinic.ru"),
        ("Новикова Ольга Александровна", "+79990001122", "novikova@clinic.ru")
    ]
    
    for fio, phone, email in doctors:
        # Проверяем, есть ли уже такой врач в базе по email
        cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
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
