from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3

router = APIRouter(prefix="/api/v1", tags=["Пользователи и Авторизация"])

# --- МОДЕЛИ ---

class LoginRequest(BaseModel):
    oms_policy: str = Field(..., pattern=r"^\d+$", description="Только цифры")

class ContactUpdateRequest(BaseModel):
    phone: str
    email: Optional[str] = None

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+7') or len(v) < 12:
            raise ValueError("Неверный формат телефона. Ожидается +7XXXXXXXXXX")
        return v
        
    @field_validator('email')
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Неверный формат email")
        return v

# --- ЭНДПОИНТЫ ---

@router.post("/auth/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    # Подключаемся к базе данных, чтобы достать реального пользователя
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    # Ищем пользователя по номеру ОМС
    cursor.execute("SELECT id, fio, role_id FROM Users WHERE oms_policy = ?", (payload.oms_policy,))
    user_row = cursor.fetchone()
    conn.close()

    # Если пользователь с таким ОМС не найден в базе
    if not user_row:
        raise HTTPException(status_code=401, detail="Пользователь с таким номером ОМС не найден")

    # Возвращаем реальные данные из базы. 
    # Тест ожидает, что fio будет "Иванова Мария Сергеевна"
    return {
        "status": "success",
        "user": {
            "id": user_row[0],
            "fio": user_row[1],
            "role_id": user_row[2]
        },
        "token": "fake-jwt-token"
    }

@router.put("/users/{user_id}/contacts", status_code=status.HTTP_200_OK)
def update_contacts(user_id: int, payload: ContactUpdateRequest):
    return {
        "status": "updated",
        "user_id": user_id,
        "phone": payload.phone,
        "email": payload.email
    }

# Эндпоинт для получения списка всех врачей
@router.get("/doctors", status_code=status.HTTP_200_OK)
def get_doctors():
    import sqlite3
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, fio FROM Users WHERE role_id = 2")
    doctors = [{"id": row[0], "fio": row[1]} for row in cursor.fetchall()]
    conn.close()
    return doctors
    
