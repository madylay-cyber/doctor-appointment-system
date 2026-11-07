import re
from typing import Optional, List, Dict, Any
from app.users.repository import UserRepository
from app.appointments.repository import AppointmentRepository
from app.models.schemas import UserModel

class UserService:
    def __init__(self, user_repo: UserRepository, appointment_repo: AppointmentRepository):
        self.user_repo = user_repo
        self.appointment_repo = appointment_repo

    def authenticate_by_oms(self, oms_policy: str) -> UserModel:
        """
        Авторизация пациента по полису ОМС [ФТ-01].
        Бизнес-правило: Полис ОМС должен строго состоять из 16 цифр.
        """
        # Чистим строку от пробелов и дефисов, если они есть
        clean_oms = re.sub(r'\s+|-', '', oms_policy)
        
        if not clean_oms.isdigit() or len(clean_oms) != 16:
            raise ValueError("Ошибка валидации: Номер полиса ОМС должен содержать ровно 16 цифр.")
            
        user = self.user_repo.get_by_oms(clean_oms)
        if not user:
            raise ValueError("Пользователь с указанным полисом ОМС не зарегистрирован в системе.")
            
        return user

    def get_patient_medical_card(self, request_user_id: int, patient_id: int) -> List[Dict[str, Any]]:
        """
        Выгрузка электронной медицинской карты (ЭМК) [ФТ-05].
        Бизнес-правило разграничения доступа:
        - Пациент может беспрепятственно смотреть свою карту.
        - Врач может смотреть карту пациента ТОЛЬКО если у него есть (или был) прием с этим пациентом.
        - Администратор (role_id = 3) имеет полный доступ.
        """
        request_user = self.user_repo.get_by_id(request_user_id)
        if not request_user:
            raise PermissionError("Пользователь не найден.")

        # Руководитель/Администратор (role_id = 3) или сам пациент
        if request_user.role_id == 3 or request_user_id == patient_id:
            return self.appointment_repo.get_medical_history(patient_id)
            
        # Если запрашивает Врач (role_id = 2)
        if request_user.role_id == 2:
            history = self.appointment_repo.get_medical_history(patient_id)
            # Проверяем, вел ли данный врач хоть один завершенный прием у этого пациента
            has_relation = any(item["doctor"] == request_user.fio for item in history)
            if not has_relation:
                raise PermissionError("Отказано в доступе: Вы не являетесь лечащим врачом данного пациента.")
            return history

        raise PermissionError("Недостаточно прав для просмотра медицинской карты.")
