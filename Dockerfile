FROM python:3.11-alpine

RUN apk add --no-cache sqlite bash

WORKDIR /app

COPY .env.example /app/.env

RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings email-validator

COPY ./app /app/app
COPY schema.sql seed.sql sqlite3.exe* /app/

RUN sqlite3 medical.db < schema.sql && sqlite3 medical.db < seed.sql

EXPOSE 8000

# Изменяем команду запуска: вызываем python напрямую как исполняемый модуль
CMD ["python", "-m", "app.main"]
