/**
 * Общие функции скрипта для MedRegistratura
 */

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // 1. Инициализация страницы входа (index.html)
    // Проверяем наличие формы входа по её классу
    if (body.querySelector('.auth-form')) {
        setupLoginHandler();
    }

    // 2. Инициализация дашборда (dashboard.html)
    // Проверяем наличие таблицы заявок
    if (body.querySelector('.table-list')) {
        initDashboard();
    }
});

/**
 * ФУНКЦИИ ДЛЯ СТРАНИЦЫ ВХОДА
 */
function setupLoginHandler() {
    const loginForm = document.querySelector('.auth-form');

    if (!loginForm) return;

    // Слушаем именно отправку формы (submit), а не просто клик
    loginForm.addEventListener('submit', function(event) {
        // Предотвращаем перезагрузку страницы (стандартное поведение формы)
        event.preventDefault(); 

        // Берем значения из полей (ID должны совпадать с HTML!)
        const omsNumber = document.getElementById('oms')?.value.trim() || '';
        const password = document.getElementById('password')?.value || '';
        const loginButton = loginForm.querySelector('button[type="submit"]');

        // Простая проверка на пустые поля
        if (!omsNumber || !password) {
            alert("⚠️ Пожалуйста, введите номер ОМС и пароль.");
            return;
        }

        console.log(`--- Попытка входа ---`);
        console.log(`Номер ОМС: ${omsNumber}`);
        
        // Меняем текст кнопки, чтобы показать загрузку
        if (loginButton) {
            loginButton.textContent = "Загрузка...";
            loginButton.disabled = true;
        }

        // Имитация запроса к серверу (задержка 800мс)
        setTimeout(() => {
            // Для теста: пропускаем любого, кто ввел хоть какие-то данные.
            // В будущем здесь будет проверка: if (omsNumber === "..." && password === "...")
            
            alert("✅ Успешный вход! Перенаправление...");
            
            // Перенаправляем на страницу дашборда
            window.location.href = 'dashboard.html'; 
            
            // Возвращаем кнопку в исходное состояние (если вдруг переход не случился)
            if (loginButton) {
                loginButton.textContent = "Войти";
                loginButton.disabled = false;
            }
        }, 800);
    });
}

/**
 * ФУНКЦИИ ДЛЯ DASHBOARD
 */
function initDashboard() {
    // В вашем HTML пока нет элементов с классом .status-filter, 
    // но если вы их добавите, этот код будет работать.
    const statusFilters = document.querySelectorAll('.status-filter');

    statusFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const selectedStatus = this.getAttribute('data-status');
            console.log(`Фильтрация по статусу: ${selectedStatus}`);
            // Здесь в будущем будет реальная фильтрация строк таблицы
        });
    });
}
