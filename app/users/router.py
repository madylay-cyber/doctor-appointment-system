from fastapi import APIRouter, HTTPException, status, Query, Path
from pydantic import BaseModel, Field, field_validator
import sqlite3
from datetime import datetime
from typing import Optional

from app.appointments.repository import AppointmentRepository
from app.users.repository import UserRepository
from app.appointments.service import AppointmentService

router = APIRouter(prefix="/api/v1", tags=["Управление Заявками и Расписанием Врачей"])

appointment_repo = AppointmentRepository("medical.db")
user_repo = UserRepository("medical.db")
appointment_service = AppointmentService(appointment_repo, user_repo)

class CreateAppointmentRequest(BaseModel):
    patient_id: int = Field(..., gt=0)
    doctor_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    datetime_slot: str = Field(..., description="Дата и время приема в формате YYYY-MM-DD HH:MM")

    @field_validator('datetime_slot')
    @classmethod
    def validate_slot_datetime(cls, v: str) -> str:
        try:
            slot_time = datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"Неверный формат даты/времени. Получено: '{v}'. Ожидается: ГГГГ-ММ-ДД ЧЧ:ММ")
        
        # Возвращаем проверку на прошлое (тест ожидает ошибку 422 при 2010 годе)
        if slot_time < datetime.now():
            raise ValueError("нельзя забронировать временной слот в прошлом.")
            
        return v

@router.post(
    "/appointments", 
    status_code=status.HTTP_201_CREATED, 
    summary="Создание новой заявки онлайн-записи (Экран 03)"
)
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Ошибка базы данных. Возможно, нет пациента (ID={payload.patient_id}) или врача (ID={payload.doctor_id})."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

# ... остальные эндпоинты (GET и DELETE) оставляем как были ...
