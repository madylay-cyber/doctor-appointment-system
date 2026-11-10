// script.js (часть, отвечающая за вход)
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.auth-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault(); 

            const omsNumber = document.getElementById('oms')?.value.trim() || '';
            const loginButton = document.querySelector('.btn-primary');

            if (!omsNumber) {
                alert("⚠️ Пожалуйста, введите номер ОМС.");
                return;
            }

            if (loginButton) {
                loginButton.textContent = "Вход...";
                loginButton.disabled = true;
            }

            try {
                // Отправляем запрос на бэкенд
                const response = await fetch('https://doctor-appointment-system-90ta.onrender.com/api/v1/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ oms_policy: omsNumber }) // Поле называется oms_policy!
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log("Успешный вход:", data);
                    // Сохраняем ID пользователя или другие данные, если они пришли в ответе
                    // localStorage.setItem('user', JSON.stringify(data)); 
                    
                    alert("✅ Успешный вход! Перенаправление...");
                    window.location.href = 'dashboard.html';
                } else {
                    const errorData = await response.json();
                    console.error("Ошибка входа:", errorData);
                    alert(`❌ Ошибка: ${errorData.detail || 'Неверный номер ОМС или пользователь не найден'}`);
                    // Возвращаем кнопку в исходное состояние
                    if (loginButton) {
                        loginButton.textContent = "Войти";
                        loginButton.disabled = false;
                    }
                }
            } catch (error) {
                console.error("Сетевая ошибка:", error);
                alert("⚠️ Не удалось связаться с сервером. Проверьте подключение.");
                if (loginButton) {
                    loginButton.textContent = "Войти";
                    loginButton.disabled = false;
                }
            }
        });
    }
});
