from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3

router = APIRouter(prefix="/api/v1", tags=["Пользователи и Авторизация"])

# --- МОДЕЛИ ДАННЫХ ---
class LoginRequest(BaseModel):
    # Теперь оба поля необязательны. Сервер поймет, что прислали.
    oms_policy: Optional[str] = None
    email: Optional[str] = None

class ContactUpdateRequest(BaseModel):
    phone: str
    email: Optional[str] = None

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+7') or len(v) < 12:
            raise ValueError("Неверный формат телефона")
        return v
        
    @field_validator('email')
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Неверный формат email")
        return v

class CreateDoctorRequest(BaseModel):
    fio: str
    phone: str
    email: Optional[str] = None

# --- ЭНДПОИНТЫ ---

@router.post("/auth/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    
    user_row = None
    # Если пришел email (Админ или Врач) - ищем по email
    if payload.email:
        cursor.execute("SELECT id, fio, role_id FROM Users WHERE email = ?", (payload.email,))
        user_row = cursor.fetchone()
    # Если пришел полис (Пациент) - ищем по полису
    elif payload.oms_policy:
        cursor.execute("SELECT id, fio, role_id FROM Users WHERE oms_policy = ?", (payload.oms_policy,))
        user_row = cursor.fetchone()
    
    conn.close()

    if not user_row:
        raise HTTPException(status_code=401, detail="Пользователь с такими данными не найден")

    return {
        "status": "success",
        "user": {
            "id": user_row[0],
            "fio": user_row[1],
            "role_id": user_row[2]
        },
        "token": "fake-jwt-token"
    }

# ... (остальной код get_doctors, create_doctor и update_contacts оставляем без изменений) ...
