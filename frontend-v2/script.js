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
    const deletedIds = JSON.parse(localStorage.getItem('deletedAppointments')) || [];
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
            console.warn("⚠️ Введите номер ОМС.");
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
   2. СОЗДАНИЕ ЗАПИСИ (book.html)
   ========================================= */
function setupBookingHandler() {
    // --- 1. Логика выбора слота времени ---
    const slots = document.querySelectorAll('.slots-grid .slot:not(.disabled)');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedDatetime = null; // Переменная для хранения выбранного времени

    slots.forEach(slot => {
        slot.addEventListener('click', function(e) {
            e.preventDefault(); 
            
            // Убираем класс active у всех слотов
            slots.forEach(s => s.classList.remove('active'));
            
            // Добавляем класс active текущему
            this.classList.add('active');
            
            // Запоминаем время из data-datetime
            selectedDatetime = this.getAttribute('data-datetime');
            const timeText = this.textContent.trim();
            
            // Обновляем текст подсказки внизу
            if (selectedSlotText) {
                selectedSlotText.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    Выбран слот: 06 ноя, ${timeText} · длительность 30 мин
                `;
                selectedSlotText.style.color = "var(--primary)";
            }
        });
    });

    // --- 2. Логика кнопки "Забронировать" ---
    const bookButton = document.getElementById('bookBtn');
    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        // Собираем данные из формы
        const patientId = document.getElementById('patientSelect')?.value;
        const categoryId = document.getElementById('categorySelect')?.value;
        const doctorRadio = document.querySelector('input[name="doctor"]:checked');

        // Проверки на заполнение
        if (!selectedDatetime) {
            console.warn("⚠️ Пожалуйста, выберите время приема!");
            return;
        }
        if (!doctorRadio) {
            console.warn("⚠️ Пожалуйста, выберите врача!");
            return;
        }

        // Формируем объект для отправки
        const appointmentData = {
            patient_id: parseInt(patientId), 
            doctor_id: parseInt(doctorRadio.value),
            category_id: parseInt(categoryId),
            datetime_slot: selectedDatetime 
        };

        console.log("Отправка данных на сервер:", appointmentData);

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
                const errorData = await response.json();
                console.error("❌ Ошибка от сервера:", errorData);
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

        // В реальном проекте эти данные тоже нужно брать из полей формы edit.html
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
                await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                console.error("Ошибка сети при удалении:", error);
            } finally {
                // В любом случае сохраняем ID и скрываем на дашборде
                const deletedIds = JSON.parse(localStorage.getItem('deletedAppointments')) || [];
                if (!deletedIds.includes(appointmentId)) {
                    deletedIds.push(appointmentId);
                    localStorage.setItem('deletedAppointments', JSON.stringify(deletedIds));
                }
                window.location.href = 'dashboard.html';
            }
        });
    }
}
