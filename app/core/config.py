from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Загрузка переменных из файла .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Переменные с дефолтными значениями на случай отсутствия .env
    app_env: str = Field("production", alias="APP_ENV")
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    debug_mode: bool = Field(False, alias="DEBUG_MODE")

    db_path: str = Field("medical.db", alias="DB_PATH")
    db_foreign_keys: bool = Field(True, alias="DB_FOREIGN_KEYS")

# Инициализируем синглтон настроек для всего приложения
settings = Settings()
