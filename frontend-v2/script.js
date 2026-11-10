/**
 * Общий скрипт для MedRegistratura
 * Интеграция с FastAPI бэкендом
 */

// Базовый URL вашего бэкенда на Render
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // 1. Инициализация страницы входа (index.html)
    if (body.querySelector('.auth-form')) {
        setupLoginHandler();
    }

    // 2. Инициализация страницы создания записи (book.html)
    if (body.querySelector('.booking-layout')) {
        setupBookingHandler();
    }

    // 3. Инициализация модального окна удаления (edit.html)
    if (body.querySelector('#deleteModal')) {
        setupDeleteHandler();
    }
});

/* =========================================
   1. СТРАНИЦА ВХОДА (index.html)
   ========================================= */
function setupLoginHandler() {
    const loginForm = document.querySelector('.auth-form');

    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); 

        const omsNumber = document.getElementById('oms')?.value.trim() || '';
        const loginButton = document.querySelector('.btn-primary');

        if (!omsNumber) {
            alert("⚠️ Пожалуйста, введите номер ОМС.");
            return;
        }

        // Блокируем кнопку на время запроса
        if (loginButton) {
            loginButton.textContent = "Вход...";
            loginButton.disabled = true;
        }

        try {
            // Отправляем POST-запрос на бэкенд
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ oms_policy: omsNumber })
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Успешный вход. Данные пользователя:", data);
                
                // Сохраняем данные пользователя в localStorage (если бэкенд их возвращает)
                // Например, чтобы потом использовать patient_id при создании записи
                localStorage.setItem('user', JSON.stringify(data));
                
                // Переходим на дашборд
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                alert(`❌ Ошибка: ${errorData.detail || errorData.message || 'Пользователь не найден'}`);
                
                // Возвращаем кнопку в исходное состояние
                if (loginButton) {
                    loginButton.textContent = "Войти";
                    loginButton.disabled = false;
                }
            }
        } catch (error) {
            console.error("Сетевая ошибка:", error);
            alert("⚠️ Сервер недоступен. Попробуйте позже.");
            if (loginButton) {
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        }
    });
}

/* =========================================
   2. СТРАНИЦА СОЗДАНИЯ ЗАПИСИ (book.html)
   ========================================= */
function setupBookingHandler() {
    // Находим кнопку "Забронировать слот"
    const bookButton = document.querySelector('.btn-primary.btn-block');

    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        // ВНИМАНИЕ: Для реальной работы здесь нужно собирать ID из выбора пользователя.
        // Поскольку сейчас в HTML нет скрытых полей для ID, мы берем условные данные.
        // В реальном проекте patient_id берется из localStorage после входа.
        
        // Пытаемся достать ID пациента из сохраненных данных (если он есть)
        const userData = JSON.parse(localStorage.getItem('user'));
        const patientId = userData?.patient_id || 1; // 1 - заглушка, если бэкенд не вернул ID

        // Берем выбранные данные из верстки (упрощенно)
        const selectedDoctorRadio = document.querySelector('input[name="doctor"]:checked');
        // Заглушка для doctor_id, так как в HTML нет value с ID врача
        const doctorId = 1; 
        const categoryId = 1; // Заглушка для category_id
        
        // Формируем дату (в реальности нужно брать из выбранного слота)
        // Бэкенд ожидает формат ISO: YYYY-MM-DDTHH:MM:SS
        const datetimeSlot = "2026-11-06T10:00:00"; 

        const appointmentData = {
            patient_id: patientId,
            doctor_id: doctorId,
            category_id: categoryId,
            datetime_slot: datetimeSlot
        };

        // Блокируем кнопку
        const originalText = bookButton.innerHTML;
        bookButton.innerHTML = "Бронирование...";
        bookButton.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(appointmentData)
            });

            if (response.status === 201 || response.ok) {
                alert("✅ Слот успешно забронирован!");
                window.location.href = 'dashboard.html';
            } else {
                const errorData = await response.json();
                alert(`❌ Ошибка бронирования: ${errorData.message || errorData.detail || 'Неизвестная ошибка'}`);
                bookButton.innerHTML = originalText;
                bookButton.disabled = false;
            }
        } catch (error) {
            console.error("Ошибка сети:", error);
            alert("⚠️ Не удалось связаться с сервером.");
            bookButton.innerHTML = originalText;
            bookButton.disabled = false;
        }
    });
}

/* =========================================
   3. УДАЛЕНИЕ ЗАПИСИ (edit.html)
   ========================================= */
function setupDeleteHandler() {
    const modal = document.getElementById('deleteModal');
    const openBtn = document.getElementById('openDeleteModal');
    const closeBtn = document.getElementById('closeModal');
    const confirmDeleteBtn = modal.querySelector('.btn-danger'); // Кнопка "Да, удалить"

    // Логика открытия/закрытия модального окна
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

    // Логика отправки DELETE запроса
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            // В реальном приложении ID записи должен браться из URL (например, ?id=1042)
            // или из data-атрибута кнопки. Здесь используем заглушку.
            const appointmentId = 1; // Заглушка. Замените на реальный ID!

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
                    alert(`❌ Ошибка удаления: ${errorData.message || errorData.detail}`);
                    confirmDeleteBtn.textContent = originalText;
                    confirmDeleteBtn.disabled = false;
                }
            } catch (error) {
                console.error("Ошибка сети:", error);
                alert("⚠️ Сервер недоступен.");
                confirmDeleteBtn.textContent = originalText;
                confirmDeleteBtn.disabled = false;
            }
        });
    }
}
