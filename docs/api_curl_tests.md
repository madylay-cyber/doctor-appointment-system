# Протокол ручного тестирования API МИС через cURL (10 запросов)

В ходе верификации ЛР №7 бэкенд-сервер обработал 10 тестовых сценариев:
1. `POST /auth/login` (Валидный ОМС Ивановой) -> `200 OK`. Успешно.
2. `POST /auth/login` (Несуществующий ОМС) -> `404 Not Found` (RESOURCE_NOT_FOUND). Успешно.
3. `POST /auth/login` (Ошибка длины ОМС) -> `422 Unprocessable Entity` (VALIDATION_ERROR). Успешно.
4. `PUT /users/5/contacts` (Обновление email) -> `200 OK`. Успешно.
5. `GET /appointments` (Выгрузка всего журнала) -> `200 OK`. Массив из 11 строк получен.
6. `GET /appointments?status_id=4` (Фильтр по статусу) -> `200 OK`. Успешно.
7. `GET /appointments?search=Петрова` (Текстовый поиск) -> `200 OK`. Успешно.
8. `POST /appointments` (Бронь слота Соколовым на 17:00) -> `201 Created` (ID: 12). Успешно.
9. `POST /appointments` (Повторная бронь на 17:00 / Race Condition) -> `409 Conflict` (SLOT_ALREADY_BOOKED). Перехвачено СУБД.
10. `DELETE /appointments/12` (Каскадная отмена приема) -> `200 OK`. Успешно удалено.
