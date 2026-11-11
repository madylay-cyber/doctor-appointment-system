/**
 * Скрипт для MedRegistratura
 */
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

console.log("🔥🔥🔥 СКРИПТ ОБНОВЛЕН: ДОБАВЛЕН ПЕРЕКЛЮЧАТЕЛЬ РОЛЕЙ!");

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // Если мы на странице входа
    if (body.querySelector('.auth-form')) {
        setupRoleSwitcher(); // Активируем кнопки ролей
        setupLoginHandler(); // Включаем логику входа
    }
    
    if (body.querySelector('.booking-layout')) setupBookingHandler();
    
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler();
        setupDeleteHandler();
    }
    
    if (body.querySelector('.detail-layout')) {
        setupDetailViewHandler();
        setupDeleteHandler();
    }
    
    if (body.querySelector('#appointmentsList')) {
        loadDashboardData();
    }
});

/* =========================================
   ПЕРЕКЛЮЧАТЕЛЬ РОЛЕЙ (index.html)
   ========================================= */
function setupRoleSwitcher() {
    const roleButtons = document.querySelectorAll('.role-btn');
    
    roleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // Чтобы форма не отправлялась при клике на роль
            
            // Убираем класс active у всех кнопок
            roleButtons.forEach(b => b.classList.remove('active'));
            // Добавляем класс active на нажатую
            this.classList.add('active');
            
            // Можно добавить логику: если выбран "Администратор", 
            // можно автоматически подставлять его ОМС (для удобства).
            const omsInput = document.getElementById('oms');
            if (this.textContent.trim() === 'Администратор' && omsInput) {
                omsInput.value = "7824 9031 5567 0012"; // ОМС Смирновой (Админа)
            } else if (this.textContent.trim() === 'Пациент' && omsInput) {
                omsInput.value = "7824 9031 5567 0012"; // В вашей БД ОМС пациента и админа могут совпадать в тестах
            }
        });
    });
}

/* =========================================
   ЗАГРУЗКА СПИСКА ВРАЧЕЙ (book.html)
   ========================================= */
async function loadDoctors() {
    const doctorListContainer = document.getElementById('doctorList');
    if (!doctorListContainer) return;

    const fallbackDoctors = [
        { id: 2, fio: "Петрова Елена Андреевна", specialization: "Кардиология" },
        { id: 3, fio: "Ким Алексей Борисович", specialization: "Терапия" },
        { id: 4, fio: "Васильев Игорь Олегович", specialization: "Офтальмология" }
    ];

    let doctors = [];

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/doctors`);
        if (response.ok) doctors = await response.json();
        else doctors = fallbackDoctors;
    } catch (error) {
        doctors = fallbackDoctors;
    }

    doctorListContainer.innerHTML = '';
    doctors.forEach((doc, index) => {
        const nameParts = doc.fio.split(' ');
        const initials = nameParts.length >= 2 ? nameParts[0][0] + nameParts[1][0] : 'ДР';
        const specialization = doc.specialization || "Врач";

        const label = document.createElement('label');
        label.className = `doctor-option ${index === 0 ? 'selected' : ''}`;
        
        label.innerHTML = `
            <div class="doctor-avatar">${initials}</div>
            <div class="doctor-info">
                <span class="doctor-name">${doc.fio}</span>
                <span class="doctor-meta">${specialization} · каб. ${200 + index}</span>
            </div>
            <input type="radio" name="doctor" value="${doc.id}" ${index === 0 ? 'checked' : ''}>
        `;
        
        label.addEventListener('click', function() {
            document.querySelectorAll('.doctor-option').forEach(el => el.classList.remove('selected'));
            this.classList.add('selected');
        });

        doctorListContainer.appendChild(label);
    });
}

/* =========================================
   ЗАГРУЗКА ДАННЫХ ДЛЯ ДАШБОРДА
   ========================================= */
async function loadDashboardData() {
    const listContainer = document.getElementById('appointmentsList');
    const countContainer = document.getElementById('recordsCount');
    if (!listContainer) return;

    listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Загрузка данных...</li>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        if (!response.ok) throw new Error(`Сервер вернул ошибку ${response.status}`);

        const appointments = await response.json();
        
        listContainer.innerHTML = '';
        if (countContainer) countContainer.textContent = appointments.length;

        if (appointments.length === 0) {
            listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Заявок пока нет.</li>';
            return;
        }

        appointments.forEach(appt => {
            let badgeClass = 'badge-secondary'; 
            const status = appt.status_name || 'Неизвестно';
            if (status === 'Подтверждено') badgeClass = 'badge-primary';
            if (status === 'В процессе') badgeClass = 'badge-warning';
            if (status === 'Завершен') badgeClass = 'badge-success';
            if (status === 'Заблокировано') badgeClass = 'badge-danger';

            const li = document.createElement('li');
            li.className = 'table-row';
            
            li.innerHTML = `
                <div class="cell" data-label="ID СЛОТА">
                    <a href="detail_view.html?id=${appt.id}" class="link">SLT-${appt.id}</a>
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

    } catch (error) {
        console.error("Ошибка загрузки данных:", error);
        listContainer.innerHTML = `<li style="padding: 20px; color: #DC2626;">Ошибка: ${error.message}</li>`;
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
   1. ВХОД (index.html)
   ========================================= */
function setupLoginHandler() {
    const loginForm = document.querySelector('.auth-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); 
        const omsNumber = document.getElementById('oms')?.value.trim() || '';
        const loginButton = document.querySelector('.btn-primary');
        
        // Определяем, какая кнопка сейчас активна (визуально)
        const activeRoleBtn = document.querySelector('.role-btn.active');
        const selectedRole = activeRoleBtn ? activeRoleBtn.textContent.trim() : "Пациент";

        if (!omsNumber) return;

        loginButton.textContent = "Вход...";
        loginButton.disabled = true;

        try {
            // Отправляем ОМС на сервер. Сервер сам поймет, кто это.
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ oms_policy: omsNumber })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('user', JSON.stringify(data));
                localStorage.setItem('selectedRole', selectedRole); // Сохраняем роль
                window.location.href = 'dashboard.html';
            } else {
                // Если ошибка, показываем красный блок (если он есть в HTML)
                const errorBlock = document.querySelector('.alert-error');
                if (errorBlock) {
                    errorBlock.style.display = 'flex';
                }
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
   2. СОЗДАНИЕ ЗАПИСИ (book.html)
   ========================================= */
function setupBookingHandler() {
    const dateTabsContainer = document.getElementById('dateTabs');
    const slots = document.querySelectorAll('.slots-grid .slot:not(.disabled)');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedTime = null; 
    let selectedDate = null; 

    loadDoctors();

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
                selectedSlotText.innerHTML = "⚠️ Пожалуйста, выберите дату, время и врача!";
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
   3. ДЕТАЛЬНЫЙ ПРОСМОТР (detail_view.html)
   ========================================= */
async function setupDetailViewHandler() {
    const headerId = document.getElementById('headerId');
    if (!headerId) return; 

    const appointmentId = getAppointmentIdFromUrl();
    document.getElementById('breadcrumbId').textContent = `SLT-${appointmentId}`;
    headerId.textContent = `SLT-${appointmentId}`;
    
    const editBtn = document.getElementById('editBtn');
    if (editBtn) editBtn.href = `edit.html?id=${appointmentId}`;
    
    const deleteIdLabel = document.getElementById('deleteIdLabel');
    if (deleteIdLabel) deleteIdLabel.textContent = `SLT-${appointmentId}`;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const appointments = await response.json();
        const appt = appointments.find(a => a.id == appointmentId);

        if (appt) {
            const [datePart, timePart] = appt.datetime_slot.split(' ');
            document.getElementById('headerSubtitle').textContent = `${datePart} · ${timePart} · ${appt.category_name}`;

            const pNameParts = appt.patient_fio.split(' ');
            const pInitials = pNameParts.length >= 2 ? pNameParts[0][0] + pNameParts[1][0] : 'ПЦ';
            document.getElementById('patientAvatar').textContent = pInitials;
            document.getElementById('patientFio').textContent = appt.patient_fio;

            const dNameParts = appt.doctor_fio.split(' ');
            const dInitials = dNameParts.length >= 2 ? dNameParts[0][0] + dNameParts[1][0] : 'ВР';
            document.getElementById('doctorAvatar').textContent = dInitials;
            document.getElementById('doctorFio').textContent = appt.doctor_fio;
            document.getElementById('doctorSpec').textContent = appt.category_name;

            const statusBadge = document.getElementById('statusBadge');
            statusBadge.innerHTML = `<span class="badge-dot"></span> ${appt.status_name || 'Подтверждено'}`;
            if (appt.status_name === 'Завершен') statusBadge.className = 'badge badge-success';
            else if (appt.status_name === 'В процессе') statusBadge.className = 'badge badge-warning';
            else if (appt.status_name === 'Заблокировано') statusBadge.className = 'badge badge-danger';
            else statusBadge.className = 'badge badge-primary';
        }
    } catch (error) {
        console.error("Ошибка загрузки деталей:", error);
        document.getElementById('headerSubtitle').textContent = "Не удалось загрузить данные";
    }
}

/* =========================================
   4. РЕДАКТИРОВАНИЕ (edit.html)
   ========================================= */
async function setupEditHandler() {
    const appointmentId = getAppointmentIdFromUrl();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const appointments = await response.json();
        const appt = appointments.find(a => a.id == appointmentId);

        if (appt) {
            if(document.getElementById('editPatientFio')) document.getElementById('editPatientFio').value = appt.patient_fio;
            if(document.getElementById('editDoctorFio')) document.getElementById('editDoctorFio').value = appt.doctor_fio;
            if(document.getElementById('editCategory')) document.getElementById('editCategory').value = appt.category_name;
            
            const [datePart, timePart] = appt.datetime_slot.split(' ');
            if(document.getElementById('editDate')) document.getElementById('editDate').value = datePart;
            if(document.getElementById('editTime')) document.getElementById('editTime').value = timePart;

            if (document.getElementById('breadcrumbId')) document.getElementById('breadcrumbId').textContent = `SLT-${appointmentId}`;
            if (document.getElementById('pageSubtitle')) document.getElementById('pageSubtitle').textContent = `SLT-${appointmentId} · редактирование`;
            if (document.getElementById('deleteIdLabel')) document.getElementById('deleteIdLabel').textContent = `SLT-${appointmentId}`;
        }
    } catch (error) {
        console.error("Ошибка загрузки для редактирования:", error);
    }
}

/* =========================================
   5. УДАЛЕНИЕ (detail_view.html и edit.html)
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
