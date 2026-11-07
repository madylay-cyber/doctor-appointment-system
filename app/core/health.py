from fastapi import APIRouter, status, HTTPException
from app.core.config import settings
import sqlite3

router = APIRouter(tags=["Системный мониторинг (Health-check)"])

@router.get(
    "/health", 
    status_code=status.HTTP_200_OK,
    summary="Проверка работоспособности системы (Health-check)",
    description="Выполняет комплексный аудит жизнедеятельности МИС: проверяет доступность веб-сервера и осуществляет тестовое подключение к СУБД SQLite."
)
def check_health():
    try:
        # Проверяем реальное подключение к СУБД
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        # Выполняем самый легкий системный запрос к SQLite
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        conn.close()
    except Exception as e:
        # Если база данных недоступна, возвращаем код 503 (Сервис недоступен)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Сбой подсистемы хранения данных (БД недоступна): {str(e)}"
        )
        
    return {
        "status": "healthy",
        "timestamp": "2026-11-07 17:32:00",
        "components": {
            "web_server": "online",
            "database": "connected"
        }
    }
