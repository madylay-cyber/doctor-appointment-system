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

    #@field_validator('datetime_slot')
    #@classmethod
    #def validate_slot_datetime(cls, v: str) -> str:
     #   try:
     #       # Проверяем только формат, но НЕ сравниваем с текущей датой
     #       datetime.strptime(v, "%Y-%m-%d %H:%M")
      #  except ValueError:
     #       raise ValueError(f"Неверный формат даты/времени. Получено: '{v}'. Ожидается: ГГГГ-ММ-ДД ЧЧ:ММ")
        
        # Возвращаем без проверки на "прошлое"
     #   return v

@router.post(
    "/appointments", 
    status_code=status.HTTP_201_CREATED, 
    summary="Создание новой заявки онлайн-записи (Экран 03)"
)
def create_appointment(payload: CreateAppointmentRequest):
    try:
        print(f"📥 Получен запрос: patient_id={payload.patient_id}, doctor_id={payload.doctor_id}, datetime={payload.datetime_slot}")
        
        appointment = appointment_service.book_online_appointment(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            category_id=payload.category_id,
            datetime_str=payload.datetime_slot
        )
        
        print(f"✅ Запись успешно создана. ID: {appointment.id}")
        return {"status": "created", "appointment_id": appointment.id, "datetime_slot": appointment.datetime_slot}
        
    except ValueError as e:
        print(f"❌ Ошибка валидации в сервисе: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except sqlite3.IntegrityError as e:
        print(f"🔥 Ошибка базы данных: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Ошибка базы данных. Возможно, нет пациента (ID={payload.patient_id}) или врача (ID={payload.doctor_id})."
        )
    except Exception as e:
        print(f"🔥 Критическая ошибка сервера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера. Проверьте логи.")

@router.get("/appointments", status_code=status.HTTP_200_OK)
def get_appointments_list(
    search: Optional[str] = Query(None),
    status_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None)
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
        query += " AND r.status_id = ?"
        params.append(status_id)
    if category_id:
        query += " AND r.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.fio LIKE ? OR d.fio LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
        
    query += " ORDER BY r.datetime_slot ASC;"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "patient_fio": row[1], "doctor_fio": row[2], "category_name": row[3], "datetime_slot": row[4], "status_name": row[5]} for row in rows]

@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_200_OK)
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
