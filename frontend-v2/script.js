/**
 * Общий скрипт для MedRegistratura
 */
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    if (body.querySelector('.auth-form')) setupLoginHandler();
    if (body.querySelector('.booking-layout')) setupBookingHandler();
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler();
        setupDeleteHandler();
    }
    if (body.querySelector('.table-list')) hideDeletedRows();
});

/* =========================================
   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
   ========================================= */
function getAppointmentIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || '1'; 
}

function hideDeletedRows() {
    const deletedIds = JSON.parse(localStorage.getItem('deletedAppointments')) || [];
    deletedIds.forEach(id => {
        const row = document.getElementById(`row-${id}`);
        if (row) row.style.display = 'none';
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
            alert("Пожалуйста, введите номер ОМС.");
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
                alert("Ошибка входа. Проверьте номер ОМС.");
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        } catch (error) {
            alert("Сервер недоступен. Попробуйте позже.");
            loginButton.textContent = "Войти";
            loginButton.disabled = false;
        }
    });
}

/* =========================================
   2. СОЗДАНИЕ ЗАПИСИ (book.html)
   ========================================= */
function setupBookingHandler() {
    // --- 1. Логика выбора времени ---
    const slots = document.querySelectorAll('.slots-grid .slot:not(.disabled)');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedTime = null; 

    slots.forEach(slot => {
        slot.addEventListener('click', function(e) {
            e.preventDefault(); 
            
            slots.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            
            // Берем только время (например, "14:00")
            selectedTime = this.getAttribute('data-time'); 
            const timeText = this.textContent.trim();
            
            if (selectedSlotText) {
                selectedSlotText.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    Выбрано время: ${timeText} · длительность 30 мин
                `;
                selectedSlotText.style.color = "var(--primary)";
            }
        });
    });

    // Устанавливаем сегодняшнюю дату в календарь по умолчанию
    const dateInput = document.getElementById('appointmentDate');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }

    // --- 2. Логика кнопки "Забронировать" ---
    const bookButton = document.getElementById('bookBtn');
    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        // Собираем данные
        const patientId = document.getElementById('patientSelect')?.value;
        const categoryId = document.getElementById('categorySelect')?.value;
        const doctorRadio = document.querySelector('input[name="doctor"]:checked');
        const selectedDate = dateInput?.value; // Получаем дату из календаря

        // Проверки
        if (!selectedDate) {
            alert("⚠️ Пожалуйста, выберите дату приема!");
            return;
        }
        if (!selectedTime) {
            alert("⚠️ Пожалуйста, выберите время (слот)!");
            return;
        }
        if (!doctorRadio) {
            alert("⚠️ Пожалуйста, выберите врача!");
            return;
        }

        // Формируем строку даты и времени в формате ISO: YYYY-MM-DDTHH:MM:00
        const datetime_slot = `${selectedDate}T${selectedTime}:00`;

        const appointmentData = {
            patient_id: parseInt(patientId), 
            doctor_id: parseInt(doctorRadio.value),
            category_id: parseInt(categoryId),
            datetime_slot: datetime_slot
        };

        console.log("Отправляем данные:", appointmentData);

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
                // Успешно создано
                window.location.href = 'dashboard.html';
            } else {
                // Сервер вернул ошибку (например, 422 или 400)
                const errorData = await response.json();
                console.error("Ошибка от сервера:", errorData);
                
                // Показываем пользователю, что именно не понравилось серверу
                let errorMsg = "Ошибка при бронировании.";
                if (errorData.detail) {
                    errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
                } else if (errorData.message) {
                    errorMsg = errorData.message;
                }
                
                alert(`❌ Не удалось забронировать:\n${errorMsg}`);
                bookButton.innerHTML = originalText;
                bookButton.disabled = false;
            }
        } catch (error) {
            console.error("Ошибка сети:", error);
            alert("⚠️ Не удалось связаться с сервером. Проверьте интернет.");
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

        const updatedData = { patient_id: 1, doctor_id: 1, category_id: 1, datetime_slot: "2026-11-06T09:30:00" };

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
                method: 'PUT', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });

            if (response.ok) window.location.href = 'dashboard.html';
            else { saveButton.textContent = originalText; saveButton.disabled = false; }
        } catch (error) {
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

    if (openBtn && closeBtn && modal) {
        openBtn.addEventListener('click', () => modal.classList.add('active'));
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('active'); });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const appointmentId = getAppointmentIdFromUrl();
            confirmDeleteBtn.textContent = "Удаление...";
            confirmDeleteBtn.disabled = true;

            try {
                await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, { method: 'DELETE' });
            } catch (error) {
                console.error("Ошибка сети:", error);
            } finally {
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
