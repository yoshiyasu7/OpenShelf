# 📚 OpenShelf API

> REST API для управления библиотечным каталогом: книги, авторы, пользователи и выдача/возврат книг.

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Быстрый старт](#-быстрый-старт)
- [Архитектура](#-архитектура)
- [Структура проекта](#-структура-проекта)
- [API эндпоинты](#-api-эндпоинты)
- [Таблицы базы данных](#-таблицы-базы-данных)
- [Конфигурация](#-конфигурация)
- [Качество и тестирование](#-качество-и-тестирование)

---

## 🎯 О проекте

**OpenShelf API** — это backend-сервис для библиотечной системы с разграничением доступа по ролям и поддержкой полного жизненного цикла книги: от создания карточки до возврата читателем.

### Основные возможности

| Функция | Описание |
|---------|----------|
| 🔐 **Аутентификация** | Регистрация, логин, refresh/logout на JWT |
| 👤 **Пользователи** | Профиль пользователя (`/me`) и админ-операции по пользователям |
| ✍️ **Авторы** | CRUD для авторов, фильтрация и валидация данных |
| 📖 **Книги** | CRUD для книг, фильтрация, управление доступными экземплярами |
| 🔄 **Выдача** | Оформление выдачи книги и возврат с обновлением остатков |
| ❤️ **Health-check** | Проверка состояния приложения и базы данных |

### Ключевые особенности

- ⚡ **Асинхронный стек**: FastAPI + SQLAlchemy Async + asyncpg.
- 🧩 **Слоистая архитектура**: `domain` → `application` → `infrastructure` → `interfaces`.
- 🛡️ **Безопасность**: JWT access/refresh + хеширование паролей (Argon2).
- ✅ **Ограничения на уровне БД**: `CHECK`, индексы, частичные индексы для активных займов и сессий.
- 🧪 **Покрытие тестами**: unit-тесты для роутеров, use-cases, репозиториев, зависимостей и инфраструктуры.

---

## 🚀 Быстрый старт

### Требования

- Python 3.14+
- Poetry
- PostgreSQL 17+ (для локального запуска без Docker)
- Docker + Docker Compose (для контейнерного запуска)

### Локальный запуск

```bash
# 1. Установка зависимостей
poetry install

# 2. Создание env
cp .env.example .env
# Заполните обязательные переменные (JWT_SECRET_KEY, JWT_ALGORITHM, DB_URL и др.)

# 3. Миграции
alembic upgrade head

# 4. Запуск приложения
make run
```

**API:** `http://127.0.0.1:8000`  
**Swagger UI:** `http://127.0.0.1:8000/docs`

### Запуск в Docker Compose

```bash
# 1. Подготовка env для deployment
cp deployment/.env.example deployment/.env
# Заполните обязательные переменные (JWT_SECRET_KEY, JWT_ALGORITHM, DB_URL и др.)

# 2. Запуск сервисов
docker compose -f deployment/docker-compose.yml up --build -d
# или
make docker-test
```

---

## 🏗 Архитектура

Проект следует слоистой архитектуре (похожа на Clean Architecture):

- `domain` — бизнес-сущности, контракты репозиториев, доменные ошибки.
- `application` — DTO и use-cases (бизнес-сценарии).
- `infrastructure` — SQLAlchemy-модели, репозитории, БД-менеджер, JWT/пароли, settings, logging.
- `interfaces` — HTTP API (FastAPI routers), health-check и точка входа приложения.

Поток запроса:

`HTTP Request -> Router -> Dependencies/Auth -> Use Case -> Repository -> PostgreSQL -> Response`

---

## 📁 Структура проекта

```text
OpenShelf/
├── pyproject.toml                 # Зависимости и tooling (Poetry, Ruff, Basedpyright)
├── Makefile                       # Команды запуска, тестов и проверок
├── Dockerfile                     # Multi-stage образ приложения
├── alembic/                       # Миграции БД
├── deployment/
│   ├── docker-compose.yml         # Контейнеры app + postgres
│   └── .env.example               # Переменные окружения для deployment
├── src/
│   ├── application/               # DTO + Use Cases
│   ├── domain/                    # Сущности, репозитории, исключения
│   ├── infrastructure/            # DB, auth, repositories, settings, logging
│   └── interfaces/                # FastAPI приложение и роутеры
└── tests/                         # Unit-тесты по слоям
```

---

## 🔌 API эндпоинты

Базовый префикс API: `/api/v1`

### Health

| Метод | Эндпоинт | Описание |
|------|----------|----------|
| GET | `/health` | Общее состояние приложения и БД |
| GET | `/health/db` | Состояние только БД |

### Authentication

| Метод | Эндпоинт | Описание | Доступ |
|------|----------|----------|--------|
| POST | `/api/v1/auth/register` | Регистрация пользователя | Public |
| POST | `/api/v1/auth/login` | Логин и выдача access/refresh | Public |
| POST | `/api/v1/auth/refresh` | Обновление токенов | Public |
| POST | `/api/v1/auth/logout` | Выход (инвалидация refresh) | Public |

### Users

| Метод | Эндпоинт | Описание | Доступ |
|------|----------|----------|--------|
| GET | `/api/v1/users/me` | Текущий пользователь | Auth |
| PATCH | `/api/v1/users/me` | Обновление своего профиля | Auth |
| DELETE | `/api/v1/users/me` | Удаление своего аккаунта | Auth |
| GET | `/api/v1/users/{user_id}` | Получение пользователя по id | Admin |
| PATCH | `/api/v1/users/{user_id}` | Обновление пользователя | Admin |
| DELETE | `/api/v1/users/{user_id}` | Удаление пользователя | Admin |

### Authors

| Метод | Эндпоинт | Описание | Доступ |
|------|----------|----------|--------|
| POST | `/api/v1/authors/` | Создание автора | Admin |
| GET | `/api/v1/authors/` | Список авторов (с фильтрацией) | Auth |
| GET | `/api/v1/authors/{author_id}` | Получение автора | Auth |
| PATCH | `/api/v1/authors/{author_id}` | Обновление автора | Admin |
| DELETE | `/api/v1/authors/{author_id}` | Удаление автора | Admin |

### Books

| Метод | Эндпоинт | Описание | Доступ |
|------|----------|----------|--------|
| POST | `/api/v1/books/` | Создание книги | Admin |
| GET | `/api/v1/books/` | Список книг (с фильтрацией) | Auth |
| GET | `/api/v1/books/{book_id}` | Получение книги | Auth |
| POST | `/api/v1/books/{book_id}/issue` | Выдача книги текущему пользователю | Auth |
| POST | `/api/v1/books/loans/{loan_id}/return` | Возврат книги | Auth |
| PATCH | `/api/v1/books/{book_id}` | Обновление книги | Admin |
| DELETE | `/api/v1/books/{book_id}` | Удаление книги | Admin |

---

## 🗃 Таблицы базы данных

Ниже перечислены таблицы, которые формируются миграциями Alembic и SQLAlchemy-моделями.

| Таблица | Назначение | Ключевые поля | Связи |
|---------|------------|---------------|-------|
| `users` | Учетные записи пользователей | `id`, `username`, `email`, `password_hash`, `is_admin`, `books_on_hand`, `created_at`, `updated_at` | `1:N` с `refresh_sessions`, `1:N` с `book_loans` |
| `refresh_sessions` | Хранение refresh-сессий (по хэшу токена) | `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at` | `N:1` к `users` |
| `authors` | Авторы книг | `id`, `name`, `biography`, `birthday`, `created_at`, `updated_at` | `M:N` с `books` через `authors_books` |
| `books` | Книги каталога | `id`, `title`, `description`, `publication_date`, `genres`, `available_instances`, `created_at`, `updated_at` | `M:N` с `authors`, `1:N` с `book_loans` |
| `authors_books` | Связка авторов и книг | `author_id`, `book_id` | `N:1` к `authors`, `N:1` к `books` |
| `book_loans` | Факты выдачи/возврата книг | `id`, `user_id`, `book_id`, `issued_at`, `due_date`, `returned_at`, `created_at`, `updated_at` | `N:1` к `users`, `N:1` к `books` |

### Важные ограничения и индексы

- `authors`: уникальность имени без учета регистра (`ux_authors_name_lower`), запрет пустого имени и лимит длины биографии.
- `books`: запрет будущей даты публикации и отрицательного количества экземпляров.
- `book_loans`: контроль корректных дат выдачи/возврата, частичные индексы для открытых займов.
- `refresh_sessions`: уникальный `token_hash`, контроль `expires_at > created_at`, частичный индекс активных сессий.

---

## ⚙️ Конфигурация

Основные файлы окружения:

- `.env.example` — локальный запуск.
- `deployment/.env.example` — запуск в Docker Compose/серверном окружении.

Ключевые группы переменных:

| Группа | Примеры | Назначение |
|--------|---------|------------|
| API | `API_HOST`, `API_PORT`, `API_DEBUG` | Параметры FastAPI/Uvicorn |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Аутентификация и срок жизни токенов |
| DB | `DB_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` | Подключение и пулы PostgreSQL |
| APP/LOG | `APP_ENV`, `LOG_LEVEL`, `LOG_TO_FILE` | Режим окружения и логирование |

---

## 🧪 Качество и тестирование

```bash
# Unit-тесты
make test

# Линт + формат + type-check
make check
```

Используется:

- `pytest`, `pytest-asyncio`
- `ruff`
- `basedpyright`
