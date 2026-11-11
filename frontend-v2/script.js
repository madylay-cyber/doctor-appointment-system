/**
 * Скрипт для MedRegistratura
 */
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    if (body.querySelector('.auth-form')) {
        setupRoleSwitcher(); setupLoginHandler(); 
    }
    if (body.querySelector('.booking-layout')) setupBookingHandler();
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler(); setupDeleteHandler();
    }
    if (body.querySelector('.detail-layout')) {
        setupDetailViewHandler(); setupDeleteHandler();
    }
    if (body.querySelector('#appointmentsList')) {
        loadDashboardData();
    }
});

/* =========================================
   ЗАГРУЗКА СПИСКА ВРАЧЕЙ (book.html)
   ========================================= */
async function loadDoctors() {
    const doctorListContainer = document.getElementById('doctorList');
    if (!doctorListContainer) return;

    // ЖЕСТКО ЗАДАЕМ ПРАВИЛЬНЫЕ ID, КАК В БАЗЕ
    const fallbackDoctors = [
        { id: 2, fio: "Петрова Елена Андреевна", specialization: "Кардиология" },
        { id: 4, fio: "Ким Алексей Борисович", specialization: "Терапия" },
        { id: 5, fio: "Васильев Игорь Олегович", specialization: "Офтальмология" }
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

function setupBookingHandler() {
    const dateTabsContainer = document.getElementById('dateTabs');
    const slotsGrid = document.getElementById('slotsGrid');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedTime = null; 
    let selectedDate = null; 

    loadDoctors();

    // Генерация дат
    if (dateTabsContainer) {
        const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
        for (let i = 1; i <= 3; i++) {
            let d = new Date();
            d.setDate(d.getDate() + i); 
            let dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; 

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

    // Генерация слотов
    const times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "14:00", "14:30", "15:00"];
    const occupiedTimes = ["09:30", "12:00", "13:00"]; 

    if (slotsGrid) {
        slotsGrid.innerHTML = '';
        times.forEach(time => {
            const btn = document.createElement('button');
            btn.type = 'button';
            const isOccupied = occupiedTimes.includes(time);
            btn.className = `slot ${isOccupied ? 'disabled' : ''}`;
            btn.textContent = time;
            btn.setAttribute('data-time', time);
            
            if (!isOccupied) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    document.querySelectorAll('.slot').forEach(s => s.classList.remove('active'));
                    this.classList.add('active');
                    selectedTime = time;
                    updateInfoText();
                });
            }
            slotsGrid.appendChild(btn);
        });
    }

    function updateInfoText() {
        if (!selectedSlotText) return;
        if (selectedDate && selectedTime) {
            selectedSlotText.innerHTML = `Выбрано: ${selectedDate}, ${selectedTime} · 30 мин`;
            selectedSlotText.style.color = "var(--primary)";
        } else if (selectedDate) {
            selectedSlotText.innerHTML = `Выбрана дата: ${selectedDate}. Теперь выберите время.`;
        } else {
            selectedSlotText.innerHTML = `Слот не выбран`;
        }
    }

    // Отправка формы
    const bookButton = document.getElementById('bookBtn');
    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        const patientId = document.getElementById('patientSelect')?.value;
        const categoryId = document.getElementById('categorySelect')?.value;
        const doctorRadio = document.querySelector('input[name="doctor"]:checked');

        if (!selectedDate || !selectedTime || !doctorRadio) {
            if (selectedSlotText) {
                selectedSlotText.innerHTML = "⚠️ Выберите дату, время и врача!";
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
                const err = await response.json();
                alert(err.detail || "Ошибка сервера");
                bookButton.innerHTML = originalText;
                bookButton.disabled = false;
            }
        } catch (error) {
            alert("Ошибка сети");
            bookButton.innerHTML = originalText;
            bookButton.disabled = false;
        }
    });
}

/* =========================================
   ОСТАЛЬНЫЕ ФУНКЦИИ (Дашборд, Детали, Вход)
   ========================================= */
function getAppointmentIdFromUrl() {
    return new URLSearchParams(window.location.search).get('id') || '1'; 
}

async function loadDashboardData() {
    const listContainer = document.getElementById('appointmentsList');
    if (!listContainer) return;
    listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Загрузка...</li>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        const appointments = await response.json();
        listContainer.innerHTML = '';
        
        if (appointments.length === 0) {
            listContainer.innerHTML = '<li style="padding: 20px; text-align: center;">Заявок пока нет.</li>';
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
                <div class="cell" data-label="ID СЛОТА"><a href="detail_view.html?id=${appt.id}" class="link">SLT-${appt.id}</a></div>
                <div class="cell" data-label="ПАЦИЕНТ"><span class="cell-main">${appt.patient_fio}</span></div>
                <div class="cell" data-label="ВРАЧ"><span class="cell-main">${appt.doctor_fio}</span><span class="cell-sub">${appt.category_name}</span></div>
                <div class="cell" data-label="ДАТА И ВРЕМЯ"><span class="cell-main">${appt.datetime_slot}</span></div>
                <div class="cell" data-label="СТАТУС"><span class="badge ${badgeClass}"><span class="badge-dot"></span> ${status}</span></div>
            `;
            listContainer.appendChild(li); 
        });
    } catch (error) {
        listContainer.innerHTML = `<li style="padding: 20px; color: red;">Ошибка загрузки</li>`;
    }
}

async function setupDetailViewHandler() {
    const appointmentId = getAppointmentIdFromUrl();
    const headerId = document.getElementById('headerId');
    if (headerId) headerId.textContent = `SLT-${appointmentId}`;
    
    let currentAppointment = null;
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        const appointments = await response.json();
        currentAppointment = appointments.find(a => a.id == appointmentId);

        if (currentAppointment) {
            const [datePart, timePart] = currentAppointment.datetime_slot.split(' ');
            document.getElementById('headerSubtitle').textContent = `${datePart} · ${timePart} · ${currentAppointment.category_name}`;
            
            document.getElementById('patientAvatar').textContent = currentAppointment.patient_fio[0];
            document.getElementById('patientFio').textContent = currentAppointment.patient_fio;
            document.getElementById('patientPhoneDisplay').textContent = currentAppointment.patient_phone ? `📞 ${currentAppointment.patient_phone}` : `📞 Номер не указан`;
            document.getElementById('patientEmailDisplay').textContent = currentAppointment.patient_email ? `✉️ ${currentAppointment.patient_email}` : `✉️ Email не указан`;

            document.getElementById('doctorFio').textContent = currentAppointment.doctor_fio;
            document.getElementById('doctorSpec').textContent = currentAppointment.category_name;

            const statusBadge = document.getElementById('statusBadge');
            statusBadge.innerHTML = `<span class="badge-dot"></span> ${currentAppointment.status_name || 'Подтверждено'}`;
            if (currentAppointment.status_name === 'Завершен') statusBadge.className = 'badge badge-success';
            else if (currentAppointment.status_name === 'В процессе') statusBadge.className = 'badge badge-warning';
            else statusBadge.className = 'badge badge-primary';
        }
    } catch (e) { console.error(e); }

    // Модалка контактов
    const modal = document.getElementById('editContactModal');
    if (document.getElementById('openEditContactsBtn') && modal) {
        document.getElementById('openEditContactsBtn').addEventListener('click', () => {
            document.getElementById('editPhoneInput').value = currentAppointment?.patient_phone || '';
            document.getElementById('editEmailInput').value = currentAppointment?.patient_email || '';
            modal.classList.add('active');
        });
        document.getElementById('closeEditContactModal').addEventListener('click', () => modal.classList.remove('active'));

        document.getElementById('saveContactBtn').addEventListener('click', async () => {
            const pId = currentAppointment?.patient_id || 6;
            const newPhone = document.getElementById('editPhoneInput').value;
            const newEmail = document.getElementById('editEmailInput').value;
            const err = document.getElementById('contactErrorMsg');
            
            try {
                const res = await fetch(`${API_BASE_URL}/api/v1/users/${pId}/contacts`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: newPhone, email: newEmail })
                });
                if (res.ok) {
                    document.getElementById('patientPhoneDisplay').textContent = `📞 ${newPhone}`;
                    document.getElementById('patientEmailDisplay').textContent = `✉️ ${newEmail}`;
                    modal.classList.remove('active');
                } else { err.style.display = 'block'; err.textContent = "Ошибка сервера"; }
            } catch (e) { err.style.display = 'block'; }
        });
    }
}

function setupDeleteHandler() {
    const modal = document.getElementById('deleteModal');
    if (document.getElementById('openDeleteModal') && modal) {
        document.getElementById('openDeleteModal').addEventListener('click', () => modal.classList.add('active'));
        document.getElementById('closeModal').addEventListener('click', () => modal.classList.remove('active'));
        document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
            const id = getAppointmentIdFromUrl();
            await fetch(`${API_BASE_URL}/api/v1/appointments/${id}`, { method: 'DELETE' });
            window.location.href = 'dashboard.html';
        });
    }
}

function setupRoleSwitcher() { /* Ваш код переключения ролей */ }
function setupLoginHandler() { /* Ваш код входа */ }
function setupEditHandler() { /* Ваш код страницы edit.html */ }
