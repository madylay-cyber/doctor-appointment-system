/**
 * Скрипт для MedRegistratura
 */
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

console.log("1. Файл script.js успешно загружен браузером.");

document.addEventListener('DOMContentLoaded', () => {
    console.log("2. Страница загружена (DOMContentLoaded).");
    const body = document.body;

    if (body.querySelector('.auth-form')) setupLoginHandler();
    if (body.querySelector('.booking-layout')) setupBookingHandler();
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler();
        setupDeleteHandler();
    }
    
    // Если мы на дашборде - загружаем реальные данные с сервера
    if (body.querySelector('#appointmentsList')) {
        console.log("3. Найден контейнер для таблицы. Запускаем загрузку данных...");
        loadDashboardData();
    } else {
        console.log("3. Контейнер для таблицы (#appointmentsList) не найден на этой странице.");
    }
});

/* =========================================
   ЗАГРУЗКА ДАННЫХ ДЛЯ ДАШБОРДА
   ========================================= */
async function loadDashboardData() {
    const listContainer = document.getElementById('appointmentsList');
    const countContainer = document.getElementById('recordsCount');
    if (!listContainer) return;

    // Принудительно меняем текст, чтобы мы точно знали, что функция начала работать
    listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Запрос отправлен. Ожидание ответа от сервера Render (может занять до 50 сек, если сервер спал)...</li>';

    try {
        console.log("4. Отправляем GET запрос на:", `${API_BASE_URL}/api/v1/appointments`);
        
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        
        console.log("5. Сервер ответил! Статус:", response.status);
        
        if (!response.ok) {
            throw new Error(`Сервер вернул ошибку ${response.status}`);
        }

        const appointments = await response.json();
        console.log("6. Данные успешно расшифрованы. Количество заявок:", appointments.length);
        
        // Очищаем контейнер
        listContainer.innerHTML = '';
        if (countContainer) countContainer.textContent = appointments.length;

        if (appointments.length === 0) {
            listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Заявок пока нет. Создайте первую!</li>';
            return;
        }

        // Генерируем строки таблицы
        appointments.forEach(appt => {
            // Определяем цвет статуса
            let badgeClass = 'badge-secondary'; 
            const status = appt.status_name || 'Неизвестно';
            if (status === 'Подтверждено') badgeClass = 'badge-primary';
            if (status === 'В процессе') badgeClass = 'badge-warning';
            if (status === 'Завершен') badgeClass = 'badge-success';
            if (status === 'Заблокировано') badgeClass = 'badge-danger';

            const li = document.createElement('li');
            li.className = 'table-row';
            
            // ВАЖНО: Ссылка на редактирование содержит реальный ID из базы (appt.id)
            li.innerHTML = `
                <div class="cell" data-label="ID СЛОТА">
                    <a href="edit.html?id=${appt.id}" class="link">SLT-${appt.id}</a>
                </div>
                <div class="cell" data-label="ПАЦИЕНТ">
                    <span class="cell-main">${appt.patient_fio}</span>
                </div>
                <div class="cell" data-label="ВРАЧ">
                    <span class="cell-main">${appt.doctor_fio}</span>
                    <span class="cell-sub">${appt.category_name}</span>
                </div>
                <div class="cell" data-label="ДАТА И ВРЕМЯ">
                    <span class="cell-main">${appt.datetime_slot}</span>
                </div>
                <div class="cell" data-label="СТАТУС">
                    <span class="badge ${badgeClass}"><span class="badge-dot"></span> ${status}</span>
                </div>
            `;
            listContainer.appendChild(li);
        });
        
        console.log("7. Таблица успешно отрисована на странице!");

    } catch (error) {
        // Если произошла ошибка - показываем её на экране
        console.error("КРИТИЧЕСКАЯ ОШИБКА при загрузке:", error);
        listContainer.innerHTML = `
            <li style="padding: 20px; text-align: center; color: #DC2626;">
                <strong>Ошибка загрузки данных</strong><br>
                ${error.message}<br>
                <span style="font-size: 12px;">Откройте консоль (F12) для подробностей.</span>
            </li>
        `;
    }
}

/* =========================================
   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
   ========================================= */
function getAppointmentIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || '1'; 
}

/* =========================================
   1. ВХОД
   ========================================= */
function setupLoginHandler() {
    const loginForm = document.querySelector('.auth-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); 
        const omsNumber = document.getElementById('oms')?.value.trim() || '';
        const loginButton = document.querySelector('.btn-primary');
        if (!omsNumber) return;

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
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        } catch (error) {
            loginButton.textContent = "Войти";
            loginButton.disabled = false;
        }
    });
}

/* =========================================
   2. СОЗДАНИЕ ЗАПИСИ
   ========================================= */
function setupBookingHandler() {
    const dateTabsContainer = document.getElementById('dateTabs');
    const slots = document.querySelectorAll('.slots-grid .slot:not(.disabled)');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedTime = null; 
    let selectedDate = null; 

    if (dateTabsContainer) {
        const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
        for (let i = 1; i <= 3; i++) {
            let d = new Date();
            d.setDate(d.getDate() + i); 
            let year = d.getFullYear();
            let month = String(d.getMonth() + 1).padStart(2, '0');
            let day = String(d.getDate()).padStart(2, '0');
            let dateStr = `${year}-${month}-${day}`; 

            let btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'date-tab';
            btn.textContent = `${d.getDate()} ${months[d.getMonth()]}`;
            btn.setAttribute('data-date', dateStr);

            btn.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.date-tab').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                selectedDate = this.getAttribute('data-date');
                updateInfoText();
            });
            dateTabsContainer.appendChild(btn);
            if (i === 1) btn.click(); 
        }
    }

    if (slots.length > 0) {
        slots.forEach(slot => {
            slot.addEventListener('click', function(e) {
                e.preventDefault(); 
                slots.forEach(s => s.classList.remove('active'));
                this.classList.add('active');
                selectedTime = this.getAttribute('data-time'); 
                updateInfoText();
            });
        });
    }

    function updateInfoText() {
        if (!selectedSlotText) return;
        if (selectedDate && selectedTime) {
            selectedSlotText.innerHTML = `Выбрано: ${selectedDate}, ${selectedTime} · длительность 30 мин`;
        } else if (selectedDate) {
            selectedSlotText.innerHTML = `Выбрана дата: ${selectedDate}. Теперь выберите время.`;
        }
        selectedSlotText.style.color = "var(--primary)";
    }

    const bookButton = document.getElementById('bookBtn');
    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        const patientId = document.getElementById('patientSelect')?.value;
        const categoryId = document.getElementById('categorySelect')?.value;
        const doctorRadio = document.querySelector('input[name="doctor"]:checked');

        if (!selectedDate || !selectedTime || !doctorRadio) {
            if (selectedSlotText) {
                selectedSlotText.innerHTML = "⚠️ Пожалуйста, выберите дату и время!";
                selectedSlotText.style.color = "#DC2626";
            }
            return;
        }

        const datetime_slot = `${selectedDate} ${selectedTime}`; 
        const appointmentData = {
            patient_id: parseInt(patientId), 
            doctor_id: parseInt(doctorRadio.value),
            category_id: parseInt(categoryId),
            datetime_slot: datetime_slot
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
                const errorData = await response.json();
                bookButton.innerHTML = "❌ Ошибка сервера";
                bookButton.style.backgroundColor = "#DC2626";
                setTimeout(() => {
                    bookButton.innerHTML = originalText;
                    bookButton.style.backgroundColor = "";
                    bookButton.disabled = false;
                }, 3000);
            }
        } catch (error) {
            bookButton.innerHTML = "❌ Ошибка сети";
            bookButton.style.backgroundColor = "#DC2626";
            setTimeout(() => {
                bookButton.innerHTML = originalText;
                bookButton.style.backgroundColor = "";
                bookButton.disabled = false;
            }, 3000);
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
            patient_id: 6, 
            doctor_id: 4,
            category_id: 4,
            datetime_slot: "2026-11-08 10:00" 
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
                saveButton.textContent = originalText;
                saveButton.disabled = false;
            }
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
                console.error("Ошибка сети при удалении:", error);
            } finally {
                window.location.href = 'dashboard.html';
            }
        });
    }
}
