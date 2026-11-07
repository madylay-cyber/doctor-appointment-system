from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator
import sqlite3
from datetime import datetime
from typing import Optional

from app.appointments.repository import AppointmentRepository
from app.users.repository import UserRepository
from app.appointments.service import AppointmentService

router = APIRouter(prefix="/api/v1", tags=["Appointments & Schedule"])

appointment_repo = AppointmentRepository("medical.db")
user_repo = UserRepository("medical.db")
appointment_service = AppointmentService(appointment_repo, user_repo)

class CreateAppointmentRequest(BaseModel):
    patient_id: int = Field(..., gt=0)
    doctor_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    datetime_slot: str = Field(..., description="Формат: YYYY-MM-DD HH:MM")

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

@router.post("/appointments", status_code=status.HTTP_201_CREATED, summary="Создание заявки на онлайн-запись (Экран 03)")
def create_appointment(payload: CreateAppointmentRequest):
    """Делегирует весь процесс онлайн-записи и проверок в AppointmentService."""
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

@router.get("/appointments", status_code=status.HTTP_200_OK, summary="Поиск и фильтрация реестра заявок (Экран 02)")
def get_appointments_list(
    search: Optional[str] = Query(None, description="Поиск по ФИО"),
    status_id: Optional[int] = Query(None, description="Фильтр по статусу"),
    category_id: Optional[int] = Query(None, description="Фильтр по категории")
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
    params = []
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
    return [{"id": r[0], "patient_fio": r[1], "doctor_fio": r[2], "category_name": r[3], "datetime_slot": r[4], "status_name": r[5]} for r in rows]

@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_200_OK, summary="Удаление/Отмена заявки с подтверждением (Экран 05)")
def delete_appointment(appointment_id: int):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Requests WHERE id = ?;", (appointment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись для удаления не найдена.")
    return {"status": "deleted", "message": f"Запись на прием №{appointment_id} окончательно стёрта."}
