from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3

router = APIRouter(prefix="/api/v1", tags=["Пользователи и Авторизация"])

class LoginRequest(BaseModel):
    oms_policy: Optional[str] = None
    email: Optional[str] = None

class ContactUpdateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator('phone')
    def validate_phone(cls, v):
        if v and (not v.startswith('+7') or len(v) < 12):
            raise ValueError("Неверный формат телефона. Ожидается +7XXXXXXXXXX")
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

@router.post("/auth/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    user_row = None
    if payload.email:
        cursor.execute("SELECT id, fio, role_id FROM Users WHERE email = ?", (payload.email,))
        user_row = cursor.fetchone()
    elif payload.oms_policy:
        cursor.execute("SELECT id, fio, role_id FROM Users WHERE oms_policy = ?", (payload.oms_policy,))
        user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        raise HTTPException(status_code=401, detail="Пользователь с такими данными не найден")

    return {
        "status": "success",
        "user": {"id": user_row[0], "fio": user_row[1], "role_id": user_row[2]},
        "token": "fake-jwt-token"
    }

@router.put("/users/{user_id}/contacts", status_code=status.HTTP_200_OK)
def update_contacts(user_id: int, payload: ContactUpdateRequest):
    conn = sqlite3.connect("medical.db", timeout=20)
    cursor = conn.cursor()
    try:
        print(f"📥 Получен запрос на обновление контактов для user_id={user_id}. Данные: {payload}")
        cursor.execute(
            "UPDATE Users SET phone = ?, email = ? WHERE id = ?",
            (payload.phone, payload.email, user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            print(f"❌ Пользователь с id={user_id} не найден в базе!")
            raise HTTPException(status_code=404, detail="Пользователь с таким ID не найден")
            
        print(f"✅ Данные для user_id={user_id} успешно сохранены в БД.")
        return {"status": "updated", "user_id": user_id, "phone": payload.phone, "email": payload.email}
    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        print(f"🔥 Ошибка БД при обновлении контактов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")
    finally:
        conn.close()

@router.get("/doctors", status_code=status.HTTP_200_OK)
def get_doctors():
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, fio, phone FROM Users WHERE role_id = 2")
    doctors = [{"id": row[0], "fio": row[1], "phone": row[2]} for row in cursor.fetchall()]
    conn.close()
    return doctors

@router.post("/doctors", status_code=status.HTTP_201_CREATED)
def create_doctor(payload: CreateDoctorRequest):
    conn = sqlite3.connect("medical.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (fio, phone, email, oms_policy, role_id) VALUES (?, ?, ?, NULL, 2)",
            (payload.fio, payload.phone, payload.email)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {"status": "success", "id": new_id, "message": "Врач успешно добавлен"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")
    finally:
        conn.close()
