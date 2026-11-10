from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3

router = APIRouter(prefix="/api/v1", tags=["Пользователи и Авторизация"])

class LoginRequest(BaseModel):
    oms_policy: str = Field(..., pattern=r"^\d+$")

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
    cursor.execute("SELECT id, fio, role_id FROM Users WHERE oms_policy = ?", (payload.oms_policy,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        raise HTTPException(status_code=401, detail="Пользователь с таким номером ОМС не найден")

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
    return {"status": "updated", "user_id": user_id, "phone": payload.phone, "email": payload.email}

# 1. ПОЛУЧИТЬ СПИСОК ВРАЧЕЙ
@router.get("/doctors", status_code=status.HTTP_200_OK)
def get_doctors():
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, fio, phone FROM Users WHERE role_id = 2")
    doctors = [{"id": row[0], "fio": row[1], "phone": row[2]} for row in cursor.fetchall()]
    conn.close()
    return doctors

# 2. ДОБАВИТЬ НОВОГО ВРАЧА
@router.post("/doctors", status_code=status.HTTP_201_CREATED)
def create_doctor(payload: CreateDoctorRequest):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    try:
        # Роль 2 = врач
        cursor.execute(
            "INSERT INTO Users (fio, phone, email, role_id) VALUES (?, ?, ?, 2)",
            (payload.fio, payload.phone, payload.email)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {"status": "success", "id": new_id, "message": "Врач успешно добавлен"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
