from fastapi import APIRouter, HTTPException, status, Path
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

from app.users.repository import UserRepository
from app.appointments.repository import AppointmentRepository
from app.users.service import UserService

router = APIRouter(prefix="/api/v1", tags=["Управление Пользователями и Авторизация"])

# Инициализируем слои данных и логики
user_repo = UserRepository("medical.db")
appointment_repo = AppointmentRepository("medical.db")
user_service = UserService(user_repo, appointment_repo)

class LoginRequest(BaseModel):
    oms_policy: str = Field(
        ..., 
        description="Уникальный 16-значный цифровой номер полиса ОМС пациента для аутентификации в МИС",
        json_schema_extra={"example": "7824903155670012"}
    )

    @field_validator('oms_policy')
    @classmethod
    def validate_oms_format(cls, v: str) -> str:
        clean_v = re.sub(r'\s+|-', '', v)
        if not clean_v.isdigit() or len(clean_v) != 16:
            raise ValueError("Полис ОМС должен состоять строго из 16 цифр.")
        return clean_v

class UpdateContactsRequest(BaseModel):
    phone: str = Field(..., description="Номер мобильного телефона в международном формате", json_schema_extra={"example": "+79214567890"})
    email: EmailStr = Field(..., description="Действующий адрес электронной почты пациента для отправки уведомлений", json_schema_extra={"example": "ivanova_new@mail.ru"})

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        if not re.match(r'^\+7\d{10}$', v):
            raise ValueError("Номер телефона должен быть строго в формате: +7 и 10 цифр.")
        return v

@router.post(
    "/auth/login", 
    status_code=status.HTTP_200_OK, 
    summary="Авторизация пациента по ОМС (Экран 01)",
    description="Принимает строку полиса ОМС, проводит её очистку и верификацию формата. При успешном поиске в СУБД инициализирует сессию пользователя."
)
def login_patient(payload: LoginRequest):
    try:
        user = user_service.authenticate_by_oms(payload.oms_policy)
        return {
            "status": "success",
            "message": "Авторизация успешно пройдена",
            "user": {"id": user.id, "fio": user.fio, "role_id": user.role_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put(
    "/users/{user_id}/contacts", 
    status_code=status.HTTP_200_OK, 
    summary="Изменение контактных данных (Экран 05)",
    description="Обновляет email и телефонный номер в профиле пациента. Проверяет корректность регулярных выражений ввода перед записью в СУБД."
)
def update_user_contacts(
    user_id: int = Path(..., gt=0, description="Уникальный числовой идентификатор пользователя в МИС"), 
    payload: UpdateContactsRequest = ...
):
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный идентификатор пользователя.")
    
    updated = user_repo.update_contacts(user_id, payload.phone, payload.email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь для обновления контактов не найден.")
    
    return {"status": "success", "message": "Контактные данные успешно обновлены в базе системы."}
