import sqlite3
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Импортируем наши изолированные API-слои (Роутеры)
from app.users.router import router as users_router
from app.appointments.router import router as appointments_router

app = FastAPI(
    title="Medical Appointment & Booking System API (Modular)",
    description="Чистый масштабируемый API-слой ИС «Система записи к врачам» (Лабораторная работа №7)",
    version="2.0.0"
)

# --- Глобальные обработчики системных исключений СУБД ---
@app.exception_handler(sqlite3.IntegrityError)
def sqlite_integrity_handler(request, exc: sqlite3.IntegrityError):
    """Аппаратный перехват Race Condition на уровне API-слоя при одновременных запросах"""
    error_msg = str(exc)
    if "UNIQUE constraint failed: Requests.doctor_id" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": "database_error", "message": "Конфликт бронирования: Этот временной слот у врача уже занят параллельным запросом."}
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "database_error", "message": "Нарушение целостности данных базы."}
    )

# --- Подключение модулей API-слоя ---
app.include_router(users_router)
app.include_router(appointments_router)
