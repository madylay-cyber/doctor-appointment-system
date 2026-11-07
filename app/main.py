import sqlite3
import os
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Импортируем роутеры API-слоя
from app.users.router import router as users_router
from app.appointments.router import router as appointments_router
from app.core.health import router as health_router

app = FastAPI(
    title="Medical Appointment & Booking System API (Cloud Ready)",
    description="Модульный API-слой ИС «Система записи к врачам» с поддержкой переменных сред Yandex/Render (Лабораторная работа №8)",
    version="2.3.0"
)

# ==========================================
# ГЛОБАЛЬНЫЙ ЕДИНООБРАЗНЫЙ СТАНДАРТ ОШИБОК
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    details = [{"field": err["loc"][-1], "issue": err["msg"]} for err in errors]
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
                "message": "Конфликт бронирования: Этот временной слот у врача уже занят другим запросом.",
                "details": None
            }
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error", "code": "DATABASE_ERROR", "message": "Нарушение целостности данных СУБД.", "details": None}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {400: "BAD_REQUEST_ERROR", 403: "FORBIDDEN_ACCESS", 404: "RESOURCE_NOT_FOUND", 503: "SERVICE_UNAVAILABLE"}
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": code_map.get(exc.status_code, "API_ERROR"), "message": exc.detail, "details": None}
    )

# Подключение модулей API-слоя
app.include_router(health_router)
app.include_router(users_router)
app.include_router(appointments_router)

# Блок интеграции веб-сервера для контейнеров облака
if __name__ == "__main__":
    import uvicorn
    cloud_port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=cloud_port)
