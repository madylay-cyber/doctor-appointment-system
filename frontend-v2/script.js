/**
 * Общие функции скрипта для MedRegistratura
 * Этот файл должен быть подключен к allen html файлам через <script src="script.js"></script>
 */

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // 1. Инициализация дашборда (dashboard.html)
    if (body.querySelector('.list-item')) {
        initDashboard();
    }

    // 2. Инициализация страницы входа (login screen - для примера)
    if (body.querySelector('#oms_number') && body.querySelector('#password')) {
        setupLoginHandler();
    }
});


/**
 * ФУНКЦИИ ДЛЯ СТРАНИЦЫ ВХОДА (На основе 01.png)
 */
function setupLoginHandler() {
    const loginButton = document.querySelector('.btn-primary'); // Предполагаемый класс кнопки "Войти"

    if (!loginButton) return;

    loginButton.addEventListener('click', function() {
        const omsNumber = document.getElementById('oms_number')?.value || '';
        const password = document.getElementById('password')?.value || '';

        // Простая клиентская проверка (ВАЖНО: реальная логика должна быть на сервере!)
        if (!omsNumber || !password) {
            alert("⚠️ Пожалуйста, введите номер ОМС и пароль.");
            return;
        }

        console.log(`--- Попытка входа ---`);
        console.log(`Номер ОМС: ${omsNumber}`);
        // Не логируем пароль для безопасности!
        
        // Имитация запроса к серверу (здесь должен быть fetch() запрос)
        if (omsNumber === "7824 9031 5567 0012" && password === "password") { // Используйте тестовые данные
            alert("✅ Успешный вход! Перенаправление...");
            // document.getElementById('main-content').style.display = 'block'; // Пример: показать контент после входа
        } else {
            alert("❌ Неверные учетные данные.");
            console.error("Ошибка аутентификации на клиенте.");
        }
    });
}


/**
 * ФУНКЦИИ ДЛЯ DASHBOARD (На основе 02.png)
 */
function initDashboard() {
    const statusFilters = document.querySelectorAll('.status-filter');

    // Добавляем обработчик клика для фильтров статуса
    statusFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const selectedStatus = this.getAttribute('data-status');
            console.log(`Фильтрация по статусу: ${selectedStatus}`);
            alert(`Имитация фильтрации: показаны только заявки со статусом "${selectedStatus}".`);
        });
    });
}
