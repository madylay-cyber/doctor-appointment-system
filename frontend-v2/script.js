const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    if (body.querySelector('.auth-form')) setupLoginHandler();
    if (body.querySelector('.booking-layout')) setupBookingHandler();
    if (body.querySelector('.edit-form-card')) {
        setupEditHandler();
        setupDeleteHandler();
    }
    
    // Если мы на дашборде - загружаем реальные данные с сервера
    if (body.querySelector('#appointmentsList')) {
        loadDashboardData();
    }
});

async function loadDashboardData() {
    const listContainer = document.getElementById('appointmentsList');
    const countContainer = document.getElementById('recordsCount');
    if (!listContainer) return;

    listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Загрузка данных...</li>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        
        if (!response.ok) {
            throw new Error(`Сервер вернул ошибку ${response.status}`);
        }

        const appointments = await response.json();
        console.log("Полученные данные:", appointments);
        
        listContainer.innerHTML = '';
        if (countContainer) countContainer.textContent = appointments.length;

        if (appointments.length === 0) {
            listContainer.innerHTML = '<li style="padding: 20px; text-align: center; color: #6B7280;">Заявок пока нет. Создайте первую!</li>';
            return;
        }

        appointments.forEach(appt => {
            let badgeClass = 'badge-secondary'; 
            if (appt.status_name === 'Подтверждено') badgeClass = 'badge-primary';
            if (appt.status_name === 'В процессе') badgeClass = 'badge-warning';
            if (appt.status_name === 'Завершен') badgeClass = 'badge-success';
            if (appt.status_name === 'Заблокировано') badgeClass = 'badge-danger';

            const li = document.createElement('li');
            li.className = 'table-row';
            
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
                    <span class="badge ${badgeClass}"><span class="badge-dot"></span> ${appt.status_name || 'Неизвестно'}</span>
                </div>
            `;
            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error("Ошибка загрузки данных:", error);
        listContainer.innerHTML = `
            <li style="padding: 20px; text-align: center; color: #DC2626;">
                <strong>Не удалось загрузить данные.</strong><br>
                Причина: ${error.message}
            </li>
        `;
    }
}

function getAppointmentIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || '1'; 
}

function setupLoginHandler() { /* ... код логина ... */ }
function setupBookingHandler() { /* ... код бронирования ... */ }
function setupEditHandler() { /* ... код редактирования ... */ }
function setupDeleteHandler() { /* ... код удаления ... */ }
