document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.auth-form');

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            // Останавливаем перезагрузку страницы
            event.preventDefault(); 

            const omsNumber = document.getElementById('oms')?.value || '';
            const password = document.getElementById('password')?.value || '';
            const loginButton = document.querySelector('.btn-primary');

            // Проверка на пустые поля (это оставляем)
            if (!omsNumber || !password) {
                alert("⚠️ Пожалуйста, введите номер ОМС и пароль.");
                return;
            }

            // Меняем текст кнопки для красоты
            if (loginButton) {
                loginButton.textContent = "Вход...";
                loginButton.disabled = true;
            }

            // СРАЗУ перенаправляем на дашборд без всплывающих окон
            window.location.href = 'dashboard.html'; 
        });
    } else {
        console.error("Форма .auth-form не найдена!");
    }
});
