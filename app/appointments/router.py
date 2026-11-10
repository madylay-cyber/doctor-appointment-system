from fastapi import APIRouter, HTTPException, status, Query, Path
from pydantic import BaseModel, Field, field_validator
import sqlite3
from datetime import datetime
from typing import Optional

# Импортируем репозитории и сервисы
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
            raise ValueError(f"Неверный формат даты/времени. Получено: '{v}'. Ожидается: ГГГГ-ММ-ДД ЧЧ:ММ")
        
        now = datetime.now()
        
        # ОТЛАДКА: Этот текст появится в логах на Render.com
        print(f"--- ВАЛИДАЦИЯ ДАТЫ ---")
        print(f"Пришло с фронтенда: {v}")
        print(f"Распознано как дата: {slot_time}")
        print(f"Текущее время сервера: {now}")
        
        if slot_time < now:
            raise ValueError(f"Нельзя забронировать временной слот в прошлом. Выбранное время: {slot_time}, Время сервера: {now}")
            
        print("✅ Валидация пройдена успешно.")
        return v

@router.post(
    "/appointments", 
    status_code=status.HTTP_201_CREATED, 
    summary="Создание новой заявки онлайн-записи (Экран 03)",
    description="Резервирует фиксированный 30-минутный временной слот к выбранному врачу. Проверяет пересечения графиков и блокирует накладки."
)
def create_appointment(payload: CreateAppointmentRequest):
    try:
        print(f"📥 Получен запрос на создание записи: {payload}")
        
        # Обращаемся к сервису. Если ошибка здесь, она попадет в except ниже.
        appointment = appointment_service.book_online_appointment(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            category_id=payload.category_id,
            datetime_str=payload.datetime_slot
        )
        
        print(f"✅ Запись успешно создана. ID: {appointment.id}")
        return {"status": "created", "appointment_id": appointment.id, "datetime_slot": appointment.datetime_slot}
        
    except ValueError as e:
        # Эта ошибка выводится в консоль браузера как 400 Bad Request
        print(f"❌ Ошибка в сервисе при создании записи: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"🔥 Неизвестная ошибка сервера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get(
    "/appointments", 
    status_code=status.HTTP_200_OK, 
    summary="Поиск и фильтрация общего реестра заявок (Экран 02)",
    description="Возвращает сводный список всех записей клиники."
)
def get_appointments_list(
    search: Optional[str] = Query(None, description="Поисковая строка"),
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

@router.delete(
    "/appointments/{appointment_id}", 
    status_code=status.HTTP_200_OK, 
    summary="Удаление/Отмена заявки с подтверждением (Экран 05)",
    description="Безвозвратно удаляет бронирование слота из СУБД."
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
