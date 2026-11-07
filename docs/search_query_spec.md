# Документация сценария фильтрации и поиска (Экран 02)

Эндпоинт `GET /api/v1/appointments` реализует динамическую сборку SQL-запроса на основе переданных клиентом Query-параметров:

```python
@router.get("/appointments", status_code=status.HTTP_200_OK, summary="Поиск и фильтрация реестра заявок (Экран 02)")
def get_appointments_list(
    search: Optional[str] = Query(None, description="Поиск по ФИО"),
    status_id: Optional[int] = Query(None, description="Фильтр по статусу"),
    category_id: Optional[int] = Query(None, description="Фильтр по категории")
):
```

### Примеры валидных запросов к API:
- `http://127.0.0` — Вывод абсолютно всех 11 записей клиники.
- `http://127.0.0?status_id=2` — Выгрузка только подтвержденных бронирований.
- `http://127.0.0?search=Иванов&category_id=1` — Поиск приемов пациентки Ивановой в отделении Кардиологии.
