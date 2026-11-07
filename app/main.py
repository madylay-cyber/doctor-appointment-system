import sqlite3
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Импортируем роутеры API-слоя
from app.users.router import router as users_router
from app.appointments.router import router as appointments_router
from app.core.health import router as health_router

app = FastAPI(
    title="Medical Appointment & Booking System API (Monitored)",
    description="Модульный API-слой ИС «Система записи к врачам» с интегрированным эндпоинтом мониторинга /health (Лабораторная работа №8)",
    version="2.2.0"
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
            "message": "Ошибка валидации входных данных. Проверьте правильность заполнения полей.",
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
                "message": "Конфликт бронирования: Этот временной слот у врача уже занят другим параллельным запросом.",
                "details": None
            }
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "code": "DATABASE_INTEGRITY_VIOLATION",
            "message": "Нарушение целостности данных на уровне ядра СУБД.",
            "details": None
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {400: "BAD_REQUEST_ERROR", 403: "FORBIDDEN_ACCESS", 404: "RESOURCE_NOT_FOUND", 503: "SERVICE_UNAVAILABLE"}
    error_code = code_map.get(exc.status_code, "API_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": error_code, "message": exc.detail, "details": None}
    )

@app.exception_handler(Exception)
async def global_internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "code": "INTERNAL_SERVER_ERROR", "message": "Произошла внутренняя системная ошибка.", "details": str(exc)}
    )

# ==========================================
# ПОДКЛЮЧЕНИЕ МОДУЛЕЙ API-СЛОЯ
# ==========================================
app.include_router(health_router)
app.include_router(users_router)
app.include_router(appointments_router)
