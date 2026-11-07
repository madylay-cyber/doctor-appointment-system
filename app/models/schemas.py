from datetime import datetime
from typing import Optional

class RoleModel:
    def __init__(self, id: int, role_name: str):
        self.id = id
        self.role_name = role_name

class UserModel:
    def __init__(self, id: int, fio: str, phone: str, email: Optional[str], oms_policy: Optional[str], role_id: int):
        self.id = id
        self.fio = fio
        self.phone = phone
        self.email = email
        self.oms_policy = oms_policy
        self.role_id = role_id

class CategoryModel:
    def __init__(self, id: int, name: str, icd_code: str):
        self.id = id
        self.name = name
        self.icd_code = icd_code

class AppointmentModel:
    def __init__(self, id: int, patient_id: int, doctor_id: int, category_id: int, status_id: int, datetime_slot: str):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.category_id = category_id
        self.status_id = status_id
        self.datetime_slot = datetime_slot  # Формат: YYYY-MM-DD HH:MM

class CommentModel:
    def __init__(self, id: int, request_id: int, author_id: int, text_content: str, created_at: str):
        self.id = id
        self.request_id = request_id
        self.author_id = author_id
        self.text_content = text_content
        self.created_at = created_at
