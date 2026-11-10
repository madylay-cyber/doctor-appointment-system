import sqlite3
import os
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.middleware.cors import CORSMiddleware

# Импортируем роутеры API-слоя
from app.users.router import router as users_router
from app.appointments.router import router as appointments_router
from app.core.health import router as health_router

app = FastAPI(
    title="Medical Appointment & Booking System API (Cloud Ready)",
    description="Модульный API-слой ИС «Система записи к врачам»",
    version="2.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://doctor-appointment-system-frontend-henna.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# АВТОМАТИЧЕСКОЕ СОЗДАНИЕ 10 ВРАЧЕЙ ПРИ СТАРТЕ
# ==========================================
@app.on_event("startup")
def init_doctors():
    print("⏳ Проверка базы данных и добавление врачей...")
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    # Создаем таблицу Users, если её вдруг нет
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
    
    # Список из 10 врачей
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
    
    added_count = 0
    for fio, phone, email in doctors:
        # Проверяем, есть ли уже такой врач в базе
        cursor.execute("SELECT id FROM Users WHERE fio = ? AND role_id = 2", (fio,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO Users (fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, 2)",
                (fio, phone, email, None)
            )
            added_count += 1
        else:
            print(f"Врач {fio} уже существует (ID: {row[0]})")
            
    conn.commit()
    
    # Выводим всех врачей с их реальными ID, чтобы вы могли сверить с фронтендом
    cursor.execute("SELECT id, fio FROM Users WHERE role_id = 2")
    all_doctors = cursor.fetchall()
    print("--- СПИСОК ВСЕХ ВРАЧЕЙ В БАЗЕ ---")
    for d in all_doctors:
        print(f"ID: {d[0]} | ФИО: {d[1]}")
    print("---------------------------------")
    
    conn.close()
    print(f"✅ Проверка завершена. Добавлено новых врачей: {added_count}")


# ==========================================
# ГЛОБАЛЬНЫЙ СТАНДАРТ ОШИБОК
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    details = [{"field": err["loc"][-1], "issue": str(err["msg"])} for err in errors]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Ошибка валидации входных данных.",
            "details": details
        }
    )

@app.exception_handler(sqlite3.IntegrityError)
async def sqlite_integrity_handler(request: Request, exc: sqlite3.IntegrityError):
    error_msg = str(exc)
    if "UNIQUE constraint failed: Requests.doctor_id" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "code": "SLOT_ALREADY_BOOKED",
                "message": "Этот временной слот у врача уже занят.",
                "details": None
            }
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error", "code": "DATABASE_ERROR", "message": "Нарушение целостности данных СУБД.", "details": None}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "BAD_REQUEST_ERROR", 
        403: "FORBIDDEN_ACCESS", 
        404: "RESOURCE_NOT_FOUND", 
        409: "CONFLICT_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error", 
            "code": code_map.get(exc.status_code, "API_ERROR"), 
            "message": error_detail, 
            "details": None
        }
    )

# Подключение модулей API-слоя
app.include_router(health_router)
app.include_router(users_router)
app.include_router(appointments_router)

# Блок запуска для Render
if __name__ == "__main__":
    import uvicorn
    cloud_port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=cloud_port)
