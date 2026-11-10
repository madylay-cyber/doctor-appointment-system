function setupBookingHandler() {
    const dateTabsContainer = document.getElementById('dateTabs');
    const slots = document.querySelectorAll('.slots-grid .slot:not(.disabled)');
    const selectedSlotText = document.getElementById('selectedSlotText');
    let selectedTime = null; 
    let selectedDate = null; // Переменная для хранения выбранной даты

    // 1. Генерируем 3 кнопки с будущими датами
    const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    
    for (let i = 1; i <= 3; i++) {
        let d = new Date();
        d.setDate(d.getDate() + i); // Прибавляем дни (завтра, послезавтра...)
        
        let year = d.getFullYear();
        let month = String(d.getMonth() + 1).padStart(2, '0');
        let day = String(d.getDate()).padStart(2, '0');
        
        let dateStr = `${year}-${month}-${day}`; // Формат для отправки: YYYY-MM-DD
        let displayDay = d.getDate();
        let displayMonth = months[d.getMonth()];

        let btn = document.createElement('button');
        btn.className = 'date-tab';
        btn.textContent = `${displayDay} ${displayMonth}`;
        btn.setAttribute('data-date', dateStr);

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.date-tab').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedDate = this.getAttribute('data-date');
            updateInfoText();
        });

        dateTabsContainer.appendChild(btn);

        // Автоматически выбираем первый день (завтра) при загрузке
        if (i === 1) {
            btn.click();
        }
    }

    // 2. Обработка выбора времени
    slots.forEach(slot => {
        slot.addEventListener('click', function(e) {
            e.preventDefault(); 
            slots.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            
            selectedTime = this.getAttribute('data-time'); 
            updateInfoText();
        });
    });

    // 3. Вспомогательная функция для обновления текста подсказки
    function updateInfoText() {
        if (selectedSlotText) {
            if (selectedDate && selectedTime) {
                selectedSlotText.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    Выбрано: ${selectedDate}, ${selectedTime} · длительность 30 мин
                `;
            } else if (selectedDate) {
                selectedSlotText.innerHTML = `Выбрана дата: ${selectedDate}. Теперь выберите время.`;
            }
            selectedSlotText.style.color = "var(--primary)";
        }
    }

    // 4. Логика кнопки "Забронировать"
    const bookButton = document.getElementById('bookBtn');
    if (!bookButton) return;

    bookButton.addEventListener('click', async function(event) {
        event.preventDefault();

        const patientId = document.getElementById('patientSelect')?.value;
        const categoryId = document.getElementById('categorySelect')?.value;
        const doctorRadio = document.querySelector('input[name="doctor"]:checked');

        if (!selectedDate || !selectedTime || !doctorRadio) {
            console.warn("⚠️ Заполните все поля (дата, время, врач).");
            return;
        }

        // Бэкенд требует строго "YYYY-MM-DD HH:MM" (через пробел)
        const datetime_slot = `${selectedDate} ${selectedTime}`; 

        const appointmentData = {
            patient_id: parseInt(patientId), 
            doctor_id: parseInt(doctorRadio.value),
            category_id: parseInt(categoryId),
            datetime_slot: datetime_slot
        };

        console.log("📤 Отправляем на сервер:", appointmentData);

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
                
                bookButton.innerHTML = "❌ Ошибка сервера";
                bookButton.style.backgroundColor = "#DC2626";
                
                setTimeout(() => {
                    bookButton.innerHTML = originalText;
                    bookButton.style.backgroundColor = "";
                    bookButton.disabled = false;
                }, 3000);
            }
        } catch (error) {
            console.error("⚠️ Ошибка сети при бронировании:", error);
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
