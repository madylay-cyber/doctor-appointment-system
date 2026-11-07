import sqlite3
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field

# Импортируем слои данных и логики, созданные на прошлых шагах
from app.users.repository import UserRepository
from app.appointments.repository import AppointmentRepository
from app.users.service import UserService
from app.appointments.service import AppointmentService

# Инициализируем FastAPI с метаданными темы проекта
app = FastAPI(
    title="Medical Appointment & Booking System API",
    description="Бэкенд-сервер автоматизации процессов записи к врачам, ведения ЭМК и управления расписанием (Лабораторная работа №6)",
    version="1.0.0"
)

# Инициализируем архитектурные слои (Dependency Injection ручного типа)
user_repo = UserRepository("medical.db")
appointment_repo = AppointmentRepository("medical.db")
user_service = UserService(user_repo, appointment_repo)
appointment_service = AppointmentService(appointment_repo, user_repo)


# ==========================================
# Pydantic-схемы для валидации запросов (Экраны 01, 03)
# ==========================================

class LoginRequest(BaseModel):
    oms_policy: str = Field(..., description="16-значный уникальный номер полиса ОМС пациента")

class CreateAppointmentRequest(BaseModel):
    patient_id: int
    doctor_id: int
    category_id: int
    datetime_slot: str = Field(..., description="Формат времени слота: ГГГГ-ММ-ДД ЧЧ:ММ")

class AddCommentRequest(BaseModel):
    author_id: int
    text_content: str


# ==========================================
# ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ И API МАРШРУТЫ
# ==========================================

@app.post("/api/v1/auth/login", status_code=status.HTTP_200_OK, summary="Сценарий: Вход в систему по ОМС (Экран 01)")
def login_patient(payload: LoginRequest):
    """
    Принимает номер полиса ОМС, проводит 16-значную валидацию на сервисном уровне
    и возвращает профиль авторизованного пациента.
    """
    try:
        user = user_service.authenticate_by_oms(payload.oms_policy)
        return {
            "status": "success",
            "message": "Авторизация успешна",
            "user": {
                "id": user.id,
                "fio": user.fio,
                "phone": user.phone,
                "role_id": user.role_id
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/api/v1/appointments", status_code=status.HTTP_201_CREATED, summary="Сценарий: Создание заявки на онлайн-запись (Экран 03)")
def create_appointment(payload: CreateAppointmentRequest):
    """
    Интерактивное резервирование 30-минутного слота времени к врачу в реальном времени.
    Проверяет роли участников, отсутствие пересечений графиков и накладок времени.
    """
    try:
        appointment = appointment_service.book_online_appointment(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            category_id=payload.category_id,
            datetime_str=payload.datetime_slot
        )
        return {
            "status": "created",
            "appointment_id": appointment.id,
            "datetime_slot": appointment.datetime_slot,
            "status_id": appointment.status_id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/api/v1/appointments", status_code=status.HTTP_200_OK, summary="Сценарий: Поиск, фильтрация и вывод списка заявок (Экран 02)")
def get_appointments_list(
    search: Optional[str] = Query(None, description="Поиск по ФИО врача или пациента"),
    status_id: Optional[int] = Query(None, description="Фильтрация по ID статуса приёма"),
    category_id: Optional[int] = Query(None, description="Фильтрация по медицинской категории (МКБ-10)")
):
    """
    Формирует динамический реестр записей МИС с поддержкой живого поиска 
    и гибкой многокритериальной фильтрации данных по аналогии с главным экраном.
    """
    # Для построения комплексного отчета с текстовыми полями используем JOIN на уровне СУБД
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    query = """
        SELECT r.id, p.fio, d.fio, c.name, r.datetime_slot, s.status_name, r.status_id, r.category_id
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
    
    return [
        {
            "id": r[0],
            "patient_fio": r[1],
            "doctor_fio": r[2],
            "category_name": r[3],
            "datetime_slot": r[4],
            "status_name": r[5]
        } for r in rows
    ]


@app.get("/api/v1/appointments/{appointment_id}", status_code=status.HTTP_200_OK, summary="Сценарий: Просмотр карточки заявки с полной информацией (Экран 04)")
def get_appointment_details(appointment_id: int):
    """
    Выводит детальные паспортные данные конкретного бронирования, 
    контакты участников, активный статус и привязанную историю переписки (чат).
    """
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    # 1. Загружаем основную информацию о приеме
    cursor.execute("""
        SELECT r.id, p.fio, p.phone, d.fio, c.name, r.datetime_slot, s.status_name, r.patient_id
        FROM Requests r
        JOIN Users p ON r.patient_id = p.id
        JOIN Users d ON r.doctor_id = d.id
        JOIN Categories c ON r.category_id = c.id
        JOIN Statuses s ON r.status_id = s.id
        WHERE r.id = ?;
    """, (appointment_id,))
    main_row = cursor.fetchone()
    
    if not main_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Запись на прием с указанным ID не найдена.")
        
    # 2. Загружаем историю связанных сообщений (внутренний чат консультации / жалобы)
    cursor.execute("""
        SELECT u.fio, rl.role_name, cm.text_content, cm.created_at
        FROM Comments cm
        JOIN Users u ON cm.author_id = u.id
        JOIN Roles rl ON u.role_id = rl.id
        WHERE cm.request_id = ?
        ORDER BY cm.created_at ASC;
    """, (appointment_id,))
    comment_rows = cursor.fetchall()
    conn.close()
    
    return {
        "appointment_id": main_row[0],
        "patient": {"fio": main_row[1], "phone": main_row[2], "id": main_row[7]},
        "doctor": {"fio": main_row[3], "specialization": main_row[4]},
        "datetime_slot": main_row[5],
        "status_name": main_row[6],
        "chat_history": [
            {"author": c[0], "role": c[1], "text": c[2], "timestamp": c[3]} for c in comment_rows
        ]
    }


@app.patch("/api/v1/appointments/{appointment_id}/status", status_code=status.HTTP_200_OK, summary="Сценарий: Редактирование и изменение статуса заявки (Экран 05)")
def update_appointment_status(appointment_id: int, new_status_id: int = Query(..., description="Новый ID статуса (1-5)")):
    """
    Редактирование состояния заявки медицинским персоналом (например, перевод в статус 'В процессе' при старте или 'Завершен' по окончании осмотра).
    """
    if new_status_id not in:
        raise HTTPException(status_code=400, detail="Неверный ID статуса. Допустимы значения от 1 до 5.")
        
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    cursor.execute("UPDATE Requests SET status_id = ? WHERE id = ?;", (new_status_id, appointment_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    
    if not updated:
        raise HTTPException(status_code=404, detail="Запись для обновления не найдена.")
        
    return {"status": "success", "message": f"Статус приема №{appointment_id} успешно обновлен на {new_status_id}"}


@app.delete("/api/v1/appointments/{appointment_id}", status_code=status.HTTP_200_OK, summary="Сценарий: Удаление/Отмена заявки с подтверждением (Экран 05)")
def delete_appointment(appointment_id: int):
    """
    Сценарий безвозвратного удаления записи из МИС администратором 
    при подтверждении опасного действия в модальном окне интерфейса.
    """
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Requests WHERE id = ?;", (appointment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись для удаления не найдена.")
        
    return {"status": "deleted", "message": f"Запись на прием №{appointment_id} окончательно стёрта из базы данных."}
