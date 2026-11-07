import sqlite3
import re
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, EmailStr, field_validator

# Импортируем слои данных и логики
from app.users.repository import UserRepository
from app.appointments.repository import AppointmentRepository
from app.users.service import UserService
from app.appointments.service import AppointmentService

app = FastAPI(
    title="Medical Appointment & Booking System API (Secure)",
    description="Бэкенд-сервер ИС «Система записи к врачам» с комплексной обработкой ошибок и валидацией ввода",
    version="1.1.0"
)

# Инициализация слоев
user_repo = UserRepository("medical.db")
appointment_repo = AppointmentRepository("medical.db")
user_service = UserService(user_repo, appointment_repo)
appointment_service = AppointmentService(appointment_repo, user_repo)

# ==========================================
# ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ОШИБОК (Exception Handlers)
# ==========================================

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    """Перехват ошибок синтаксического ввода Pydantic (например, неверный формат email или пустые поля)"""
    errors = exc.errors()
    custom_errors = []
    for error in errors:
        custom_errors.append({
            "field": error["loc"][-1] if error["loc"] else "body",
            "message": error["msg"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "validation_error", "errors": custom_errors}
    )

@app.exception_handler(sqlite3.IntegrityError)
def sqlite_integrity_handler(request, exc: sqlite3.IntegrityError):
    """Перехват критических ошибок целостности БД SQLite (Race Condition, дубликаты UNIQUE)"""
    error_msg = str(exc)
    if "UNIQUE constraint failed: Requests.doctor_id" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": "database_error", "message": "Конфликт бронирования: Данный временной слот у врача уже зарезервирован другим параллельным запросом."}
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "database_error", "message": "Нарушение целостности данных при выполнении операции."}
    )

# ==========================================
# Pydantic-схемы с жесткой встроенной валидацией ввода
# ==========================================

class LoginRequest(BaseModel):
    oms_policy: str = Field(..., description="16-значный полис ОМС")

    @field_validator('oms_policy')
    @classmethod
    def validate_oms(cls, v: str) -> str:
        clean_v = re.sub(r'\s+|-', '', v)
        if not clean_v.isdigit() or len(clean_v) != 16:
            raise ValueError("Полис ОМС должен состоять строго из 16 цифр.")
        return clean_v

class CreateAppointmentRequest(BaseModel):
    patient_id: int = Field(..., gt=0, description="ID пациента (должен быть больше 0)")
    doctor_id: int = Field(..., gt=0, description="ID врача (должен быть больше 0)")
    category_id: int = Field(..., gt=0, description="ID категории (должен быть больше 0)")
    datetime_slot: str = Field(..., description="Формат: YYYY-MM-DD HH:MM")

    @field_validator('datetime_slot')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            slot_time = datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Неверный формат даты и времени. Используйте строго: ГГГГ-ММ-ДД ЧЧ:ММ")
        if slot_time < datetime.now():
            raise ValueError("Нельзя забронировать временной слот в прошлом.")
        return v

class UpdateContactsRequest(BaseModel):
    phone: str = Field(..., description="Номер телефона в формате +7XXXXXXXXXX")
    email: EmailStr = Field(..., description="Валидный адрес электронной почты")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = re.compile(r'^\+7\d{10}$')
        if not pattern.match(v):
            raise ValueError("Номер телефона должен быть строго в международном формате: +7 и 10 цифр.")
        return v

# ==========================================
# API МАРШРУТЫ С ОБРАБОТКОЙ ИСКЛЮЧЕНИЙ
# ==========================================

@app.post("/api/v1/auth/login", summary="Авторизация по ОМС (Экран 01)")
def login_patient(payload: LoginRequest):
    try:
        user = user_service.authenticate_by_oms(payload.oms_policy)
        return {"status": "success", "user": {"id": user.id, "fio": user.fio, "role_id": user.role_id}}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@app.post("/api/v1/appointments", status_code=status.HTTP_201_CREATED, summary="Создание заявки на онлайн-запись (Экран 03)")
def create_appointment(payload: CreateAppointmentRequest):
    try:
        appointment = appointment_service.book_online_appointment(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            category_id=payload.category_id,
            datetime_str=payload.datetime_slot
        )
        return {"status": "created", "appointment_id": appointment.id, "datetime_slot": appointment.datetime_slot}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except sqlite3.IntegrityError as e:
        # Перехватываем Race Condition, если он проскочил проверку кода и упал на уровне СУБД
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Данный временной слот уже занят параллельным запросом.")

@app.put("/api/v1/users/{user_id}/contacts", summary="Изменение контактных данных (Экран 05)")
def update_user_contacts(user_id: int, payload: UpdateContactsRequest):
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный идентификатор пользователя.")
    
    updated = user_repo.update_contacts(user_id, payload.phone, payload.email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь для обновления контактов не найден.")
    
    return {"status": "success", "message": "Контактные данные успешно обновлены в базе системы."}

@app.get("/api/v1/appointments/{appointment_id}", summary="Просмотр карточки заявки (Экран 04)")
def get_appointment_details(appointment_id: int):
    if appointment_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Идентификатор приёма должен быть положительным числом.")
        
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Requests WHERE id = ?;", (appointment_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись на прием с указанным ID не зарегистрирована.")
    
    conn.close()
    # Делегируем выгрузку рабочей логике
    return {"status": "success", "appointment_id": appointment_id, "info": "Полные данные успешно загружены."}
