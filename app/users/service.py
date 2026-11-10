from datetime import datetime
from app.appointments.repository import AppointmentRepository
from app.users.repository import UserRepository
from app.models.schemas import AppointmentModel

class AppointmentService:
    def __init__(self, appointment_repo: AppointmentRepository, user_repo: UserRepository):
        self.appointment_repo = appointment_repo
        self.user_repo = user_repo

    def book_online_appointment(self, patient_id: int, doctor_id: int, category_id: int, datetime_str: str) -> AppointmentModel:
        # 1. Проверяем существование и роли участников
        patient = self.user_repo.get_by_id(patient_id)
        doctor = self.user_repo.get_by_id(doctor_id)
        
        if not patient or patient.role_id != 1:
            raise ValueError("Указанный ID пациента некорректен или пользователь не является пациентом.")
        if not doctor or doctor.role_id != 2:
            raise ValueError("Указанный ID врача некорректен или пользователь не является медицинским специалистом.")

        # 2. Проверяем формат времени слота
        try:
            slot_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Неверный формат времени. Ожидается: ГГГГ-ММ-ДД ЧЧ:ММ")

        # Бизнес-правило: Нельзя записаться на прошедшее время (ВОЗВРАЩЕНО)
        if slot_time < datetime.now():
            raise ValueError("нельзя забронировать временной слот в прошлом.")

        # 3. Защита от Race Condition
        if self.appointment_repo.check_slot_conflict(doctor_id, datetime_str):
            raise ValueError("Выбранное время уже занято другим пациентом или заблокировано администратором.")

        # 4. Проводим запись
        appointment = self.appointment_repo.create_appointment(patient_id, doctor_id, category_id, datetime_str)
        
        # 5. Триггер коммуникаций
        self._send_notification_stub(patient.fio, f"Вы успешно записаны к врачу на {datetime_str}.")
        
        return appointment

    def block_slots_for_vacation(self, admin_user_id: int, doctor_id: int, start_date: str, end_date: str) -> int:
        admin = self.user_repo.get_by_id(admin_user_id)
        if not admin or admin.role_id != 3:
            raise PermissionError("Только администратор клиники имеет право блокировать расписание.")

        doctor = self.user_repo.get_by_id(doctor_id)
        if not doctor or doctor.role_id != 2:
            raise ValueError("Указанный пользователь не является врачом.")

        return self.appointment_repo.block_doctor_slots(doctor_id, start_date, end_date)

    def _send_notification_stub(self, phone: str, message: str):
        print(f"[SMS-NOTIFY] Отправка на номер {phone}: '{message}' — Успешно доставлено.")
