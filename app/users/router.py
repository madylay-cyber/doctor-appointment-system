from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

from app.users.repository import UserRepository
from app.appointments.repository import AppointmentRepository
from app.users.service import UserService

router = APIRouter(prefix="/api/v1", tags=["Users & Authentication"])

# Инициализируем зависимости
user_repo = UserRepository("medical.db")
appointment_repo = AppointmentRepository("medical.db")
user_service = UserService(user_repo, appointment_repo)

# --- Pydantic Схемы валидации ввода (Уровень API) ---
class LoginRequest(BaseModel):
    oms_policy: str = Field(..., description="16-значный уникальный номер полиса ОМС")

    @field_validator('oms_policy')
    @classmethod
    def validate_oms_format(cls, v: str) -> str:
        clean_v = re.sub(r'\s+|-', '', v)
        if not clean_v.isdigit() or len(clean_v) != 16:
            raise ValueError("Полис ОМС должен состоять строго из 16 цифр.")
        return clean_v

class UpdateContactsRequest(BaseModel):
    phone: str = Field(..., description="Номер телефона в международном формате +7XXXXXXXXXX")
    email: EmailStr = Field(..., description="Валидный адрес электронной почты")

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        if not re.match(r'^\+7\d{10}$', v):
            raise ValueError("Номер телефона должен быть строго в формате: +7 и 10 цифр.")
        return v

# --- API Эндпоинты ---
@router.post("/auth/login", status_code=status.HTTP_200_OK, summary="Авторизация по ОМС (Экран 01)")
def login_patient(payload: LoginRequest):
    """Принимает ОМС, валидирует структуру на уровне API и передает в UserService без дублирования логики."""
    try:
        user = user_service.authenticate_by_oms(payload.oms_policy)
        return {
            "status": "success",
            "message": "Авторизация успешна",
            "user": {"id": user.id, "fio": user.fio, "role_id": user.role_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/users/{user_id}/contacts", status_code=status.HTTP_200_OK, summary="Изменение контактных данных (Экран 05)")
def update_user_contacts(user_id: int, payload: UpdateContactsRequest):
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный идентификатор пользователя.")
    
    updated = user_repo.update_contacts(user_id, payload.phone, payload.email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь для обновления контактов не найден.")
    
    return {"status": "success", "message": "Контактные данные успешно обновлены."}
