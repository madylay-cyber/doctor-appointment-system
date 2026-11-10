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
    // Проверяем наличие элемента, который есть только на этой странице
    if (body.querySelector('.edit-form-card')) {
        console.log("Страница редактирования загружена. Инициализация...");
        setupEditHandler();
        setupDeleteHandler();
    }
});

/* =========================================
   ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Получение ID из URL
   ========================================= */
function getAppointmentIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id') || '1'; // По умолчанию 1
    console.log("Используемый ID записи:", id);
    return id; 
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
    // Ищем кнопку по ID, который мы добавили в HTML
    const saveButton = document.getElementById('saveChangesBtn');

    if (!saveButton) {
        console.error("ОШИБКА: Кнопка с id='saveChangesBtn' не найдена в HTML!");
        return;
    }

    saveButton.addEventListener('click', async function(event) {
        event.preventDefault();
        console.log("Кнопка 'Сохранить изменения' нажата!"); // Проверка клика

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
            console.log(`Отправка PUT запроса на ${API_BASE_URL}/api/v1/appointments/${appointmentId}`);
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                method: 'PUT', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });

            console.log("Ответ сервера:", response.status);

            if (response.ok) {
                alert("✅ Изменения успешно сохранены!");
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                console.error("Ошибка от сервера:", errorData);
                alert(`❌ Ошибка сохранения: ${errorData.message || 'Проверьте данные'}`);
                saveButton.textContent = originalText;
                saveButton.disabled = false;
            }
        } catch (error) {
            console.error("Критическая ошибка:", error);
            alert("⚠️ Сервер недоступен или заблокирован запрос (CORS).");
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
    // Ищем кнопку по ID
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // Открытие/закрытие окна
    if (openBtn && closeBtn && modal) {
        openBtn.addEventListener('click', () => {
            console.log("Модальное окно открыто.");
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
            console.log("Кнопка 'Да, удалить' нажата!"); // Проверка клика
            const appointmentId = getAppointmentIdFromUrl();
            
            const originalText = confirmDeleteBtn.textContent;
            confirmDeleteBtn.textContent = "Удаление...";
            confirmDeleteBtn.disabled = true;

            try {
                console.log(`Отправка DELETE запроса на ${API_BASE_URL}/api/v1/appointments/${appointmentId}`);
                const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });

                console.log("Ответ сервера:", response.status);

                if (response.ok) {
                    alert("✅ Запись успешно удалена.");
                    window.location.href = 'dashboard.html';
                } else {
                    const errorData = await response.json();
                    console.error("Ошибка от сервера:", errorData);
                    alert(`❌ Ошибка удаления: ${errorData.message || 'Запись не найдена'}`);
                    confirmDeleteBtn.textContent = originalText;
                    confirmDeleteBtn.disabled = false;
                }
            } catch (error) {
                console.error("Критическая ошибка:", error);
                alert("⚠️ Сервер недоступен или заблокирован запрос (CORS).");
                confirmDeleteBtn.textContent = originalText;
                confirmDeleteBtn.disabled = false;
            }
        });
    } else {
        console.error("ОШИБКА: Кнопка с id='confirmDeleteBtn' не найдена в HTML!");
    }
}
