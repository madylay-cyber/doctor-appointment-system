import pytest
from fastapi.testclient import TestClient

# =====================================================================
# КАТЕГОРИЯ 1: Тесты бизнес-логики и основных функций (Не менее 3)
# =====================================================================

def test_logic_login_success(client: TestClient):
    """Тест: Успешная авторизация пациента по существующему ОМС (Экран 01)."""
    response = client.post("/api/v1/auth/login", json={"oms_policy": "7824903155670012"})
    assert response.status_code in [200, 201]
    assert response.json()["status"] == "success"
    assert "Иванова Мария Сергеевна" in response.json()["user"]["fio"]

def test_logic_get_appointments_registry(client: TestClient):
    """Тест: Выгрузка полного журнала медицинских приёмов клиники (Экран 02)."""
    response = client.get("/api/v1/appointments")
    assert response.status_code in [200, 201]
    assert isinstance(response.json(), list)

def test_logic_create_appointment_slot(client: TestClient):
    """Тест: Резервирование нового свободного слота времени онлайн-записи (Экран 03)."""
    payload = {
        "patient_id": 6,
        "doctor_id": 4,
        "category_id": 4,
        "datetime_slot": "2026-11-20 14:00"
    }
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code in [200, 201]

# =====================================================================
# КАТЕГОРИЯ 2: Тесты API (Успешный, Ошибочный ввод, Отсутствующий ресурс) (Не менее 3)
# =====================================================================

def test_api_search_doctor_filter(client: TestClient):
    """Тест API: Успешная фильтрация журнала по ФИО лечащего врача."""
    response = client.get("/api/v1/appointments?search=Петрова")
    assert response.status_code in [200, 201]

def test_api_login_validation_error(client: TestClient):
    """Тест API: Ошибочный синтаксический ввод букв вместо 16 цифр ОМС."""
    response = client.post("/api/v1/auth/login", json={"oms_policy": "invalid-policy-abc"})
    assert response.status_code in [400, 422]

def test_api_delete_non_existent_resource(client: TestClient):
    """Тест API: Попытка отмены/удаления несуществующей в СУБД заявки."""
    response = client.delete("/api/v1/appointments/9999")
    assert response.status_code in [400, 404, 422]

# =====================================================================
# КАТЕГОРИЯ 3: Валидация и негативные сценарии (Не менее 2)
# =====================================================================

def test_validation_update_contacts_invalid_phone(client: TestClient):
    """Тест валидации: Нарушение международной маски телефона регулярного выражения Pydantic."""
    payload = {"phone": "8-921-123-45", "email": "ivanova@mail.ru"}
    response = client.put("/api/v1/users/5/contacts", json=payload)
    assert response.status_code in [400, 422]

def test_validation_update_contacts_broken_email(client: TestClient):
    """Тест валидации: Нарушение структуры и отсутствие знака @ в поле EmailStr."""
    payload = {"phone": "+79214567890", "email": "broken_email_domain"}
    response = client.put("/api/v1/users/5/contacts", json=payload)
    assert response.status_code in [400, 422]

# =====================================================================
# КАТЕГОРИЯ 4: Регрессионные тесты рискованных требований (Не менее 2)
# =====================================================================

def test_regression_booking_in_past_blocked(client: TestClient):
    """Регрессионный тест: Блокировка попытки бронирования слотов в прошедшем времени."""
    payload = {
        "patient_id": 6,
        "doctor_id": 4,
        "category_id": 4,
        "datetime_slot": "2010-01-01 10:00"
    }
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code in [400, 422]

def test_regression_race_condition_hardware_blocked(client: TestClient):
    """Регрессионный тест: Аппаратный перехват СУБД состояния гонки (Race Condition / Двойная бронь)."""
    payload = {
        "patient_id": 5,
        "doctor_id": 2,
        "category_id": 1,
        "datetime_slot": "2026-11-20 10:30"
    }
    # Первый клик
    res1 = client.post("/api/v1/appointments", json=payload)
    assert res1.status_code in [200, 201, 400]
    
    # Второй параллельный клик
    res2 = client.post("/api/v1/appointments", json=payload)
    assert res2.status_code in [400, 409]
