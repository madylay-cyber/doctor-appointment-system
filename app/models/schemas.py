# Сущности предметной области информационной системы

class User:
    """Общие данные пользователей (ФИО, телефон, email)"""
    def __init__(self, user_id: int, fio: str, phone: str, email: str, role: str):
        self.user_id = user_id
        self.fio = fio
        self.phone = phone
        self.email = email
        self.role = role  # Пациент, Врач, Администратор, Менеджер

class Specialist:
    """Данные о медицинском сотруднике"""
    def __init__(self, doctor_id: int, user_id: int, specialization: str, working_hours: str):
        self.doctor_id = doctor_id
        self.user_id = user_id
        self.specialization = specialization
        self.working_hours = working_hours

class Appointment:
    """Прием (Запись на слот времени)"""
    def __init__(self, appointment_id: int, patient_id: int, doctor_id: int, start_time: str, status: str):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.start_time = start_time
        self.status = status  # Подтверждено / Отменено / В процессе / Завершен

class MedicalCard:
    """Электронная медицинская карта пациента"""
    def __init__(self, card_id: int, patient_id: int, diagnoses: list, treatments: list, conclusions: list):
        self.card_id = card_id
        self.patient_id = patient_id
        self.diagnoses = diagnoses  # Коды МКБ-10
        self.treatments = treatments
        self.conclusions = conclusions
