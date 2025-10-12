# Log Analyzer - Сервис анализа логов в реальном времени

Управление и анализ логов через REST API.  
Поддержка аутентификации, фильтрации, статистики и очистки старых записей.

---

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
````

### 2. Настройка окружения

Создай файл `.env` на основе шаблона:

```bash
cp .env.example .env
```

Заполни значения (например, `SECRET_KEY` можно сгенерировать через `openssl rand -hex 32`).

### 3. Запуск сервера

```bash
uvicorn app.main:app --reload
```

Сервер запустится на `http://localhost:8000`.

---

## Тестирование

Запусти юнит-тесты:

```bash
pytest -v
```

---

## Эндпоинты

### Аутентификация

#### Регистрация пользователя

```http
POST /auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "securepass123"
}
```

#### Вход

```http
POST /auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "securepass123"
}
```

→ Возвращает `access_token`.

---

### Логи

#### Добавить лог

```http
POST /add_log
Authorization: Bearer <токен>
Content-Type: application/json

{
  "timestamp": "2025-05-14T12:00:00Z",
  "level": "INFO",
  "service": "auth_service",
  "message": "User logged in",
  "metadata": {
    "user_id": 1,
    "ip": "192.168.1.1"
  }
}
```

#### Получить логи (с фильтрами)

```http
GET /logs?level=ERROR&start_time=2025-05-14T00:00:00Z&end_time=2025-05-15T00:00:00Z&limit=10&offset=0
Authorization: Bearer <токен>
```

Ответ:

```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-05-14T12:00:00Z",
      "level": "ERROR",
      "service": "db_service",
      "message": "Connection timeout",
      "metadata": {
        "host": "192.168.1.10",
        "port": 5432
      }
    }
  ],
  "total": 1
}
```

---

### Статистика

#### Получить статистику по уровням

```http
GET /stats?group_by=level
Authorization: Bearer <токен>
```

Ответ:

```json
{
  "stats": [
    { "level": "ERROR", "count": 1 },
    { "level": "INFO", "count": 5 }
  ]
}
```

---

### Очистка логов (только администратор)

```http
DELETE /logs?before=2025-05-14T00:00:00Z
Authorization: Bearer <токен_админа>
```

Ответ:

```json
{
  "deleted": 500
}
```

> Только пользователь с именем `admin` может удалять логи.

---

## Docker (опционально)

Собери образ:

```bash
docker build -t log-analyzer .
```

Запусти контейнер:

```bash
docker run -p 8000:8000 log-analyzer
```

---

## Структура проекта

```
log_analyzer/
├── app/               # Ядро приложения
│   ├── api/           # Роутеры
│   ├── core/          # Безопасность, JWT
│   ├── crud/          # Операции с БД
│   ├── models/        # Pydantic-схемы
│   ├── schemas/       # SQLAlchemy-модели
│   └── main.py        # Точка входа
├── tests/             # Юнит-тесты
├── alembic/           # Миграции
├── logs/              # Файл логов (автоматически создаётся)
├── .env.example       # Шаблон переменных окружения
├── requirements.txt   # Зависимости
└── README.md          # Этот файл
```

---

## Лицензия

MIT - свободное использование и распространение.
