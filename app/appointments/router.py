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
    patient_id: int = Field(..., gt=0, description="Идентификатор записывающегося пациента")
    doctor_id: int = Field(..., gt=0, description="Идентификатор принимающего медицинского специалиста")
    category_id: int = Field(..., gt=0, description="Идентификатор категории услуги (МКБ-10)")
    datetime_slot: str = Field(..., description="Дата и время приема в формате YYYY-MM-DD HH:MM", json_schema_extra={"example": "2026-11-08 17:00"})

    @field_validator('datetime_slot')
    @classmethod
    def validate_slot_datetime(cls, v: str) -> str:
        try:
            slot_time = datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Неверный формат даты/времени. Ожидается: ГГГГ-ММ-ДД ЧЧ:ММ")
        if slot_time < datetime.now():
            raise ValueError("Нельзя забронировать временной слот в прошлом.")
        return v

@router.post(
    "/appointments", 
    status_code=status.HTTP_201_CREATED, 
    summary="Создание новой заявки онлайн-записи (Экран 03)",
    description="Резервирует фиксированный 30-минутный временной интервал к выбранному врачу. Проверяет пересечения графиков и блокирует накладки."
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

@router.get(
    "/appointments", 
    status_code=status.HTTP_200_OK, 
    summary="Поиск и фильтрация общего реестра заявок (Экран 02)",
    description="Возвращает сводный список всех записей клиники. Поддерживает сквозной поиск по части ФИО и фильтры по направлениям и статусам приёма."
)
def get_appointments_list(
    search: Optional[str] = Query(None, description="Поисковая строка для фильтрации по подстроке ФИО врача или пациента"),
    status_id: Optional[int] = Query(None, description="Фильтр по цифровому коду состояния приема (1-5) из справочника статусов"),
    category_id: Optional[int] = Query(None, description="Фильтр по идентификатору медицинской специализации (МКБ-10)")
):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    query = """
        SELECT r.id, p.fio, d.fio, c.name, r.datetime_slot, s.status_name
        FROM Requests r
        JOIN Users p ON r.patient_id = p.id
        JOIN Users d ON r.doctor_id = d.id
        JOIN Categories c ON r.category_id = c.id
        JOIN Statuses s ON r.status_id = s.id
        WHERE 1=1
    """
    params =
    if status_id:
        query += " AND r.status_id = ?"; params.append(status_id)
    if category_id:
        query += " AND r.category_id = ?"; params.append(category_id)
    if search:
        query += " AND (p.fio LIKE ? OR d.fio LIKE ?)"; params.append(f"%{search}%"); params.append(f"%{search}%")
        
    query += " ORDER BY r.datetime_slot ASC;"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r, "patient_fio": r, "doctor_fio": r, "category_name": r, "datetime_slot": r, "status_name": r} for r in rows]

@router.delete(
    "/appointments/{appointment_id}", 
    status_code=status.HTTP_200_OK, 
    summary="Удаление/Отмена заявки с подтверждением (Экран 05)",
    description="Безвозвратно удаляет бронирование слота из СУБД. Применяет каскадное удаление (ON DELETE CASCADE) ко всей переписке в чате приема."
)
def delete_appointment(
    appointment_id: int = Path(..., gt=0, description="Уникальный числовой идентификатор удаляемого приёма")
):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Requests WHERE id = ?;", (appointment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись для удаления не найдена в базе данных.")
    return {"status": "deleted", "message": f"Запись на прием №{appointment_id} окончательно стёрта из системы."}
