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
    print("⏳ Очистка и пересоздание базы данных...")
    conn = sqlite3.connect("medical.db", timeout=20)
    cursor = conn.cursor()
    
    # УДАЛЯЕМ ВСЕ СТАРЫЕ ТАБЛИЦЫ
    cursor.execute("DROP TABLE IF EXISTS Requests")
    cursor.execute("DROP TABLE IF EXISTS Users")
    cursor.execute("DROP TABLE IF EXISTS Categories")
    cursor.execute("DROP TABLE IF EXISTS Statuses")
    
    # СОЗДАЕМ ЗАНОВО
    cursor.execute("CREATE TABLE Users (id INTEGER PRIMARY KEY AUTOINCREMENT, fio TEXT, phone TEXT, email TEXT, oms_policy TEXT UNIQUE, role_id INTEGER)")
    cursor.execute("CREATE TABLE Categories (id INTEGER PRIMARY KEY, name TEXT, icd_code TEXT)")
    cursor.execute("CREATE TABLE Statuses (id INTEGER PRIMARY KEY, status_name TEXT)")
    cursor.execute("CREATE TABLE Requests (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, doctor_id INTEGER, category_id INTEGER, status_id INTEGER, datetime_slot TEXT)")
    
    # ДОБАВЛЯЕМ АДМИНА
    cursor.execute("INSERT INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, ?, 3)", (3, "Смирнова Анна Викторовна", "+79990000000", "smirnova@clinic.ru", "0000000000000000"))
    # ДОБАВЛЯЕМ ИВАНОВУ
    cursor.execute("INSERT INTO Users (id, fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, ?, ?, 1)", (6, "Иванова Мария Сергеевна", "+79214567890", "ivanova@mail.ru", "7824903155670012"))
    # ВРАЧИ
    cursor.execute("INSERT INTO Users (id, fio, phone, email, role_id) VALUES (2, 'Петрова Елена Андреевна', '+79991112233', 'petrova@clinic.ru', 2)")
    cursor.execute("INSERT INTO Users (id, fio, phone, email, role_id) VALUES (4, 'Ким Алексей Борисович', '+79992223344', 'kim@clinic.ru', 2)")
    
    conn.commit()
    conn.close()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"status": "error", "message": "Ошибка валидации"})

@app.exception_handler(sqlite3.IntegrityError)
async def sqlite_integrity_handler(request: Request, exc: sqlite3.IntegrityError):
    return JSONResponse(status_code=400, content={"status": "error", "message": "Ошибка БД"})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": str(exc.detail)})

app.include_router(health_router)
app.include_router(users_router)
app.include_router(appointments_router)
