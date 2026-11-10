/**
 * Общий скрипт для MedRegistratura
 */

// Базовый URL вашего бэкенда
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // 1. Вход (index.html)
    if (body.querySelector('.auth-form')) {
        setupLoginHandler();
    }

    // 2. Создание записи (book.html)
    if (body.querySelector('.booking-layout')) {
        setupBookingHandler();
    }

    // 3. Редактирование и Удаление (edit.html)
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler();
        setupDeleteHandler();
    }
});

/* =========================================
   ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Получение ID из URL
   ========================================= */
function getAppointmentIdFromUrl() {
    // Ищем параметр ?id=... в адресной строке
    const urlParams = new URLSearchParams(window.location.search);
    // Если ID нет (например, вы открыли файл напрямую), ставим дефолтный для теста
    return urlParams.get('id') || '1042'; 
}

/* =========================================
   1. ВХОД
   ========================================= */
function setupLoginHandler() {
    const loginForm = document.querySelector('.auth-form');

    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); 
        const omsNumber = document.getElementById('oms')?.value.trim() || '';
        const loginButton = document.querySelector('.btn-primary');

        if (!omsNumber) {
            alert("⚠️ Введите номер ОМС.");
            return;
        }

        loginButton.textContent = "Вход...";
        loginButton.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ oms_policy: omsNumber })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('user', JSON.stringify(data));
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                alert(`❌ Ошибка: ${errorData.detail || 'Неверные данные'}`);
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        } catch (error) {
            alert("⚠️ Сервер недоступен.");
            loginButton.textContent = "Войти";
            loginButton.disabled = false;
        }
    });
}

/* =========================================
   2. СОЗДАНИЕ ЗАПИСИ
   ========================================= */
function setupBookingHandler() {
    const bookButton = document.querySelector('.btn-block.btn-primary');

    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();
        
        // В реальности эти ID должны браться из выпадающих списков
        const appointmentData = {
            patient_id: 1, 
            doctor_id: 1,
            category_id: 1,
            datetime_slot: "2026-11-06T10:00:00" 
        };

        const originalText = bookButton.innerHTML;
        bookButton.innerHTML = "Бронирование...";
        bookButton.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(appointmentData)
            });

            if (response.ok) {
                alert("✅ Слот успешно забронирован!");
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                alert(`❌ Ошибка: ${errorData.message || 'Не удалось создать'}`);
                bookButton.innerHTML = originalText;
                bookButton.disabled = false;
            }
        } catch (error) {
            alert("⚠️ Ошибка сети.");
            bookButton.innerHTML = originalText;
            bookButton.disabled = false;
        }
    });
}

/* =========================================
   3. РЕДАКТИРОВАНИЕ (Кнопка "Сохранить изменения")
   ========================================= */
function setupEditHandler() {
    const saveButton = document.querySelector('.edit-form-card .btn-primary');

    if (!saveButton) return;

    saveButton.addEventListener('click', async function(event) {
        event.preventDefault();
        
        const appointmentId = getAppointmentIdFromUrl();
        const originalText = saveButton.textContent;
        saveButton.textContent = "Сохранение...";
        saveButton.disabled = true;

        // Собираем данные из формы (упрощенно, для примера)
        const updatedData = {
            patient_id: 1, // В реальности брать из select
            doctor_id: 1,
            category_id: 1,
            datetime_slot: "2026-11-06T09:30:00"
        };

        try {
            // Отправляем PUT запрос (или PATCH, в зависимости от бэкенда)
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                method: 'PUT', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });

            if (response.ok) {
                alert("✅ Изменения успешно сохранены!");
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                alert(`❌ Ошибка сохранения: ${errorData.message || 'Проверьте данные'}`);
                saveButton.textContent = originalText;
                saveButton.disabled = false;
            }
        } catch (error) {
            alert("⚠️ Сервер недоступен.");
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        }
    });
}

/* =========================================
   4. УДАЛЕНИЕ (Модальное окно)
   ========================================= */
function setupDeleteHandler() {
    const modal = document.getElementById('deleteModal');
    const openBtn = document.getElementById('openDeleteModal');
    const closeBtn = document.getElementById('closeModal');
    const confirmDeleteBtn = modal?.querySelector('.btn-danger');

    // Открытие/закрытие окна
    if (openBtn && closeBtn) {
        openBtn.addEventListener('click', () => {
            modal.classList.add('active');
            modal.setAttribute('aria-hidden', 'false');
        });

        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
                modal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    // Само удаление
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const appointmentId = getAppointmentIdFromUrl();
            
            const originalText = confirmDeleteBtn.textContent;
            confirmDeleteBtn.textContent = "Удаление...";
            confirmDeleteBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    alert("✅ Запись успешно удалена.");
                    window.location.href = 'dashboard.html';
                } else {
                    const errorData = await response.json();
                    alert(`❌ Ошибка удаления: ${errorData.message || 'Запись не найдена'}`);
                    confirmDeleteBtn.textContent = originalText;
                    confirmDeleteBtn.disabled = false;
                }
            } catch (error) {
                alert("⚠️ Сервер недоступен.");
                confirmDeleteBtn.textContent = originalText;
                confirmDeleteBtn.disabled = false;
            }
        });
    }
}
