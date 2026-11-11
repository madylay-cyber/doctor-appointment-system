/**
 * Скрипт для MedRegistratura
 */
const API_BASE_URL = 'https://doctor-appointment-system-90ta.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    if (body.querySelector('.auth-form')) {
        setupRoleSwitcher(); 
        setupLoginHandler(); 
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

// ... (функции setupRoleSwitcher, loadDoctors, loadDashboardData, getAppointmentIdFromUrl, setupLoginHandler, setupBookingHandler остаются без изменений, они уже есть у вас) ...
// Я напишу только обновленную функцию setupDetailViewHandler и setupEditHandler (так как в ней тоже были алерты).

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

    let currentAppointment = null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/appointments`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const appointments = await response.json();
        currentAppointment = appointments.find(a => a.id == appointmentId);

        if (currentAppointment) {
            const [datePart, timePart] = currentAppointment.datetime_slot.split(' ');
            document.getElementById('headerSubtitle').textContent = `${datePart} · ${timePart} · ${currentAppointment.category_name}`;

            const pNameParts = currentAppointment.patient_fio.split(' ');
            const pInitials = pNameParts.length >= 2 ? pNameParts[0][0] + pNameParts[1][0] : 'ПЦ';
            document.getElementById('patientAvatar').textContent = pInitials;
            document.getElementById('patientFio').textContent = currentAppointment.patient_fio;
            
            // ВЫВОДИМ ТЕЛЕФОН ИЗ БАЗЫ
            const phoneDisplay = document.getElementById('patientPhoneDisplay');
            if (phoneDisplay) {
                phoneDisplay.textContent = currentAppointment.patient_phone ? `📞 ${currentAppointment.patient_phone}` : `📞 Номер не указан`;
            }

            const dNameParts = currentAppointment.doctor_fio.split(' ');
            const dInitials = dNameParts.length >= 2 ? dNameParts[0][0] + dNameParts[1][0] : 'ВР';
            document.getElementById('doctorAvatar').textContent = dInitials;
            document.getElementById('doctorFio').textContent = currentAppointment.doctor_fio;
            document.getElementById('doctorSpec').textContent = currentAppointment.category_name;

            const statusBadge = document.getElementById('statusBadge');
            statusBadge.innerHTML = `<span class="badge-dot"></span> ${currentAppointment.status_name || 'Подтверждено'}`;
            if (currentAppointment.status_name === 'Завершен') statusBadge.className = 'badge badge-success';
            else if (currentAppointment.status_name === 'В процессе') statusBadge.className = 'badge badge-warning';
            else if (currentAppointment.status_name === 'Заблокировано') statusBadge.className = 'badge badge-danger';
            else statusBadge.className = 'badge badge-primary';
        }
    } catch (error) {
        console.error("Ошибка загрузки деталей:", error);
        document.getElementById('headerSubtitle').textContent = "Не удалось загрузить данные";
    }

    // --- ЛОГИКА ИЗМЕНЕНИЯ КОНТАКТОВ ---
    const editContactModal = document.getElementById('editContactModal');
    const openEditBtn = document.getElementById('openEditContactsBtn');
    const closeEditBtn = document.getElementById('closeEditContactModal');
    const saveContactBtn = document.getElementById('saveContactBtn');
    const editPhoneInput = document.getElementById('editPhoneInput');
    const editEmailInput = document.getElementById('editEmailInput');
    const errorMsg = document.getElementById('contactErrorMsg');

    if (openEditBtn && editContactModal) {
        // Открытие окна и ПОДСТАНОВКА ТЕКУЩИХ ДАННЫХ
        openEditBtn.addEventListener('click', () => {
            if (!currentAppointment) return;
            editPhoneInput.value = currentAppointment.patient_phone || '';
            editEmailInput.value = currentAppointment.patient_email || '';
            errorMsg.style.display = 'none'; // Скрываем старую ошибку
            editContactModal.classList.add('active');
        });

        closeEditBtn.addEventListener('click', () => {
            editContactModal.classList.remove('active');
        });

        editContactModal.addEventListener('click', (e) => {
            if (e.target === editContactModal) editContactModal.classList.remove('active');
        });

        // СОХРАНЕНИЕ
        saveContactBtn.addEventListener('click', async () => {
            if (!currentAppointment) return;
            
            const newPhone = editPhoneInput.value.trim();
            const newEmail = editEmailInput.value.trim();

            // Проверка формата телефона (бэкенд требует +7 и минимум 12 символов)
            if (!newPhone.startsWith('+7') || newPhone.length < 12) {
                errorMsg.textContent = "Ошибка: формат телефона должен быть +7XXXXXXXXXX";
                errorMsg.style.display = 'block';
                return;
            }

            errorMsg.style.display = 'none';
            saveContactBtn.textContent = "Сохранение...";
            saveContactBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/users/${currentAppointment.patient_id}/contacts`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: newPhone, email: newEmail })
                });

                if (response.ok) {
                    // Обновляем текст на странице
                    if (document.getElementById('patientPhoneDisplay')) {
                        document.getElementById('patientPhoneDisplay').textContent = `📞 ${newPhone}`;
                    }
                    editContactModal.classList.remove('active');
                } else {
                    errorMsg.textContent = "Ошибка сервера при сохранении.";
                    errorMsg.style.display = 'block';
                }
            } catch (error) {
                errorMsg.textContent = "Ошибка сети. Сервер недоступен.";
                errorMsg.style.display = 'block';
            } finally {
                saveContactBtn.textContent = "Сохранить";
                saveContactBtn.disabled = false;
            }
        });
    }
}

/* =========================================
   4. РЕДАКТИРОВАНИЕ (edit.html)
   ========================================= */
async function setupEditHandler() {
    const appointmentId = getAppointmentIdFromUrl();
    const saveButton = document.getElementById('saveChangesBtn');
    
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

    // Сохранение на странице edit.html (тоже без алертов)
    if (saveButton) {
        saveButton.addEventListener('click', async function(event) {
            event.preventDefault();
            const originalText = saveButton.textContent;
            saveButton.textContent = "Сохранение...";
            saveButton.disabled = true;

            // Отправляем те же данные (заглушка)
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
                    saveButton.textContent = "❌ Ошибка сохранения";
                    saveButton.style.backgroundColor = "#DC2626";
                    setTimeout(() => {
                        saveButton.textContent = originalText;
                        saveButton.style.backgroundColor = "";
                        saveButton.disabled = false;
                    }, 3000);
                }
            } catch (error) {
                saveButton.textContent = "❌ Ошибка сети";
                saveButton.style.backgroundColor = "#DC2626";
                setTimeout(() => {
                    saveButton.textContent = originalText;
                    saveButton.style.backgroundColor = "";
                    saveButton.disabled = false;
                }, 3000);
            }
        });
    }
}

// ... (Функция setupDeleteHandler остается без изменений) ...
