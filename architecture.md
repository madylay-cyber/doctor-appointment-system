# Архитектурное проектирование системы

## Жизненный цикл заявки на бронирование слота
Стадии: Инициация ➔ Подтверждение ➔ Проведение приема (В процессе) ➔ Завершение.

1. **Инициация (Создание):** Пациент выбирает врача через ЛК или Администратор вносит запись вручную при экстренной ситуации.
2. **Валидация (Обработка):** Система автоматически проверяет доступность слота, отсутствие конфликтов и соответствие специализации.
3. **Жизненный цикл статусов:** 
   - Пациент может отменить/перенести запись.
   - Администратор может перевести в статус "Заблокировано".
   - Врач переводит статус в "В процессе" при старте приема и в "Завершен" после осмотра.
4. **Контроль результата:** Врач оставляет электронное заключение в ЭМК, система делает его доступным для непрерывности лечения.

## Use Case Диаграмма (Mermaid)
```mermaid
idwc
actor Patient as "Пациент"
actor Doctor as "Врач"
actor Admin as "Администратор"

VisualClient --> Patient
VisualClient --> Doctor
VisualClient --> Admin

graph TD
    Patient -->|Запись на прием| Slot[Выбор слота времени]
    Patient -->|Отмена/Перенос| Cancel[Управление записью]
    Doctor -->|Просмотр ЭМК| History[История болезни]
    Doctor -->|Заключение| Status[Изменение статуса: Завершен]
    Admin -->|Блокировка слотов| Block[Управление календарем]
    Admin -->|Отчет| Report[Отчет по загруженности]
```

---

## 🗄 Реляционная схема базы данных (ER-Диаграмма)

Проектирование структуры данных выполнено в соответствии с правилами **3-й нормальной формы (3NF)**. Ниже представлена интерактивная ER-диаграмма сущностей, первичных (PK) и внешних (FK) ключей:

```mermaid
erDiagram
    Roles ||--o{ Users : "has"
    Users ||--o{ Requests : "books (as patient)"
    Users ||--o{ Requests : "conducts (as doctor)"
    Users ||--o{ Comments : "writes"
    Categories ||--o{ Requests : "classified under"
    Statuses ||--o{ Requests : "tracks state"
    Requests ||--o{ Comments : "contains"

    Roles {
        integer id PK
        string role_name NN
    }
    Users {
        integer id PK
        string fio NN
        string phone NN
        string email
        string oms_policy UNIQUE
        integer role_id FK
    }
    Categories {
        integer id PK
        string name NN
        string icd_code UNIQUE
    }
    Statuses {
        integer id PK
        string status_name NN
    }
    Requests {
        integer id PK
        integer patient_id FK
        integer doctor_id FK
        integer category_id FK
        integer status_id FK
        datetime datetime_slot NN
    }
    Comments {
        integer id PK
        integer request_id FK
        integer author_id FK
        string text_content NN
        datetime created_at NN
    }
```
