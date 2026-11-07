# 1. Используем официальный легковесный образ Python на базе дистрибутива Alpine Linux
FROM python:3.11-alpine

# 2. Устанавливаем системные утилиты для корректной сборки пакетов и работы SQLite3
RUN apk add --no-cache sqlite bash

# 3. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 4. Копируем файл зависимостей (шаблон окружения) внутрь контейнера
COPY .env.example /app/.env

# 5. Устанавливаем все необходимые библиотеки Python одной командой
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings email-validator

# 6. Копируем исходный код бэкенда и файлы конфигурации базы данных
COPY ./app /app/app
COPY schema.sql seed.sql sqlite3.exe* /app/

# 7. Автоматически инициализируем и наполняем базу данных тестовыми 11 заявками при сборке образа
RUN sqlite3 medical.db < schema.sql && sqlite3 medical.db < seed.sql

# 8. Открываем сетевой порт 8000, на котором будет работать наше API
EXPOSE 8000

# 9. Инструкция для запуска ASGI-сервера Uvicorn при старте контейнера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
