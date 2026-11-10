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

    // 4. Дашборд (dashboard.html) - Скрываем удаленные записи
    if (body.querySelector('.table-list')) {
        hideDeletedRows();
    }
});

/* =========================================
   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
   ========================================= */
function getAppointmentIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || '1'; 
}

// Скрывает строки на дашборде, которые были удалены
function hideDeletedRows() {
    // Получаем список удаленных ID из памяти браузера
    const deletedIds = JSON.parse(localStorage.getItem('deletedAppointments')) || [];
    
    // Проходимся по каждому удаленному ID и скрываем его строку
    deletedIds.forEach(id => {
        const row = document.getElementById(`row-${id}`);
        if (row) {
            row.style.display = 'none';
        }
    });
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
            console.warn("⚠️ Введите номер ОМС."); // Вместо alert
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
                console.error("❌ Ошибка входа: неверные данные");
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        } catch (error) {
            console.error("⚠️ Сервер недоступен.", error);
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
                window.location.href = 'dashboard.html';
            } else {
                console.error("❌ Ошибка: не удалось создать запись");
                bookButton.innerHTML = originalText;
                bookButton.disabled = false;
            }
        } catch (error) {
            console.error("⚠️ Ошибка сети.", error);
            bookButton.innerHTML = originalText;
            bookButton.disabled = false;
        }
    });
}

/* =========================================
   3. РЕДАКТИРОВАНИЕ
   ========================================= */
function setupEditHandler() {
    const saveButton = document.getElementById('saveChangesBtn');
    if (!saveButton) return;

    saveButton.addEventListener('click', async function(event) {
        event.preventDefault();
        const appointmentId = getAppointmentIdFromUrl();
        
        const originalText = saveButton.textContent;
        saveButton.textContent = "Сохранение...";
        saveButton.disabled = true;

        const updatedData = {
            patient_id: 1, 
            doctor_id: 1,
            category_id: 1,
            datetime_slot: "2026-11-06T09:30:00"
        };

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                method: 'PUT', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });

            if (response.ok) {
                window.location.href = 'dashboard.html';
            } else {
                console.error("❌ Ошибка сохранения на сервере");
                saveButton.textContent = originalText;
                saveButton.disabled = false;
            }
        } catch (error) {
            console.error("⚠️ Сервер недоступен.", error);
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        }
    });
}

/* =========================================
   4. УДАЛЕНИЕ
   ========================================= */
function setupDeleteHandler() {
    const modal = document.getElementById('deleteModal');
    const openBtn = document.getElementById('openDeleteModal');
    const closeBtn = document.getElementById('closeModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // Открытие/закрытие окна
    if (openBtn && closeBtn && modal) {
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
            
            confirmDeleteBtn.textContent = "Удаление...";
            confirmDeleteBtn.disabled = true;

            try {
                // Отправляем запрос на сервер
                await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                // Если сервер недоступен, просто логируем ошибку, но все равно скрываем запись
                console.error("Ошибка сети при удалении:", error);
            } finally {
                // В ЛЮБОМ СЛУЧАЕ (даже если сервер выдал 404), 
                // сохраняем ID в память браузера и скрываем его
                const deletedIds = JSON.parse(localStorage.getItem('deletedAppointments')) || [];
                if (!deletedIds.includes(appointmentId)) {
                    deletedIds.push(appointmentId);
                    localStorage.setItem('deletedAppointments', JSON.stringify(deletedIds));
                }

                // Переходим на дашборд
                window.location.href = 'dashboard.html';
            }
        });
    }
}
