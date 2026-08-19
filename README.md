# 📚 OpenShelf API

> REST API for managing a library catalog: books, authors, users, and book checkout/return.

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)

---

🇺🇸 EN | [🇷🇺 RU](./README_ru.md)

---

## 📋 Table of Contents

- [About](#-about)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Database Tables](#-database-tables)
- [Configuration](#-configuration)
- [Quality and Testing](#-quality-and-testing)

---

## 🎯 About

**OpenShelf API** is a backend service for a library system with role-based access control and full book lifecycle support: from creating a catalog entry to returning it by a reader.

### Core Features

| Feature | Description |
|---------|-------------|
| 🔐 **Authentication** | Registration, login, refresh/logout with JWT |
| 👤 **Users** | User profile (`/me`) and admin user operations |
| ✍️ **Authors** | CRUD for authors, filtering, and data validation |
| 📖 **Books** | CRUD for books, filtering, available copy management |
| 🔄 **Loans** | Book checkout and return with inventory updates |
| ❤️ **Health-check** | Application and database health checks |

### Key Highlights

- ⚡ **Async stack**: FastAPI + SQLAlchemy Async + asyncpg.
- 🧩 **Clean Architecture**: domain and use cases are independent of FastAPI, SQLAlchemy, and other external details.
- 🛡️ **Security**: JWT access/refresh + password hashing (Argon2).
- ✅ **Database constraints**: `CHECK`, indexes, partial indexes for active loans and sessions.
- 🧪 **Test coverage**: unit tests for routers, use cases, repositories, dependencies, and infrastructure.

---

## 🚀 Quick Start

### Requirements

- Python 3.14+
- Poetry
- PostgreSQL 17+ (for local runs without Docker)
- Docker + Docker Compose (for containerized runs)

### Local Run

```bash
# 1. Install dependencies
poetry install

# 2. Create env
cp .env.example .env
# Fill in required variables (JWT_SECRET_KEY, JWT_ALGORITHM, DB_URL, etc.)

# 3. Migrations
alembic upgrade head

# 4. Start the application
make run
```

**API:** `http://127.0.0.1:8000`  
**Swagger UI:** `http://127.0.0.1:8000/docs`

### Docker Compose Run

```bash
# 1. Prepare env for deployment
cp deployment/.env.example deployment/.env
# Fill in required variables (JWT_SECRET_KEY, JWT_ALGORITHM, DB_URL, etc.)

# 2. Start services
docker compose -f deployment/docker-compose.yml up --build -d
# or
make docker-test
```

---

## 🏗 Architecture

The project follows **Clean Architecture** principles: business rules live in inner layers, while external details (FastAPI, SQLAlchemy, PostgreSQL, JWT library, Argon2) are wired through adapters.

### Layers

| Layer | Path | Responsibility |
|------|------|----------------|
| **Domain** | `src/domain/` | Domain entities, errors, and abstract repository contracts |
| **Application** | `src/application/` | Use cases, DTOs, and ports for external services |
| **Infrastructure** | `src/infrastructure/` | SQLAlchemy models, repositories, JWT, Argon2, database manager, settings, logging |
| **Interfaces** | `src/interfaces/` | FastAPI application, routers, HTTP interaction schemas |
| **Composition / DI** | `src/dependencies/` | Wires use cases to concrete infrastructure adapters |

### Dependency Rule

Inner layers do not depend on outer layers:

- `domain` does not import FastAPI, SQLAlchemy, or infrastructure.
- `application` works with abstractions: `BookRepository`, `UserRepository`, `TokenService`, `PasswordHasher`, `RefreshSessionStore`.
- `infrastructure` implements these contracts via SQLAlchemy, JWT, and Argon2.
- `interfaces` accepts HTTP requests and delegates work to use cases through FastAPI dependencies.

Request flow:

```text
HTTP Request
  -> FastAPI Router (interfaces)
  -> Dependencies / DI
  -> Use Case (application)
  -> Port / Repository Contract
  -> Infrastructure Adapter
  -> PostgreSQL / JWT / Argon2
```

---

## 📁 Project Structure

```text
OpenShelf/
├── pyproject.toml                 # Dependencies and tooling (Poetry, Ruff, Basedpyright)
├── Makefile                       # Run, test, and check commands
├── Dockerfile                     # Multi-stage application image
├── alembic/                       # DB migrations
├── deployment/
│   ├── docker-compose.yml         # app + postgres containers
│   └── .env.example               # Environment variables for deployment
├── src/
│   ├── application/               # Use Cases, DTO, ports
│   ├── domain/                    # Entities, repository contracts, exceptions
│   ├── infrastructure/            # Adapters: DB, auth, repositories, settings, logging
│   ├── dependencies/              # Dependency Injection / composition root
│   └── interfaces/                # FastAPI application and routers
└── tests/                         # Unit tests by layer
```

---

## 🔌 API Endpoints

Base API prefix: `/api/v1`

### Health

| Method | Endpoint | Description |
|------|----------|-------------|
| GET | `/health` | Overall application and DB status |
| GET | `/health/db` | DB status only |

### Authentication

| Method | Endpoint | Description | Access |
|------|----------|-------------|--------|
| POST | `/api/v1/auth/register` | Register a user | Public |
| POST | `/api/v1/auth/login` | Login and issue access/refresh tokens | Public |
| POST | `/api/v1/auth/refresh` | Refresh tokens | Public |
| POST | `/api/v1/auth/logout` | Logout (invalidate refresh token) | Public |

### Users

| Method | Endpoint | Description | Access |
|------|----------|-------------|--------|
| GET | `/api/v1/users/me` | Current user | Auth |
| PATCH | `/api/v1/users/me` | Update own profile | Auth |
| DELETE | `/api/v1/users/me` | Delete own account | Auth |
| GET | `/api/v1/users/{user_id}` | Get user by id | Admin |
| PATCH | `/api/v1/users/{user_id}` | Update user | Admin |
| DELETE | `/api/v1/users/{user_id}` | Delete user | Admin |

### Authors

| Method | Endpoint | Description | Access |
|------|----------|-------------|--------|
| POST | `/api/v1/authors/` | Create author | Admin |
| GET | `/api/v1/authors/` | List authors (with filtering) | Auth |
| GET | `/api/v1/authors/{author_id}` | Get author | Auth |
| PATCH | `/api/v1/authors/{author_id}` | Update author | Admin |
| DELETE | `/api/v1/authors/{author_id}` | Delete author | Admin |

### Books

| Method | Endpoint | Description | Access |
|------|----------|-------------|--------|
| POST | `/api/v1/books/` | Create book | Admin |
| GET | `/api/v1/books/` | List books (with filtering) | Auth |
| GET | `/api/v1/books/{book_id}` | Get book | Auth |
| POST | `/api/v1/books/{book_id}/issue` | Issue book to current user | Auth |
| POST | `/api/v1/books/loans/{loan_id}/return` | Return book | Auth |
| PATCH | `/api/v1/books/{book_id}` | Update book | Admin |
| DELETE | `/api/v1/books/{book_id}` | Delete book | Admin |

---

## 🗃 Database Tables

The tables below are created by Alembic migrations and SQLAlchemy models.

| Table | Purpose | Key Fields | Relations |
|---------|------------|---------------|-------|
| `users` | User accounts | `id`, `username`, `email`, `password_hash`, `is_admin`, `books_on_hand`, `created_at`, `updated_at` | `1:N` with `refresh_sessions`, `1:N` with `book_loans` |
| `refresh_sessions` | Refresh session storage (by token hash) | `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at` | `N:1` to `users` |
| `authors` | Book authors | `id`, `name`, `biography`, `birthday`, `created_at`, `updated_at` | `M:N` with `books` via `authors_books` |
| `books` | Catalog books | `id`, `title`, `description`, `publication_date`, `genres`, `available_instances`, `created_at`, `updated_at` | `M:N` with `authors`, `1:N` with `book_loans` |
| `authors_books` | Author–book link | `author_id`, `book_id` | `N:1` to `authors`, `N:1` to `books` |
| `book_loans` | Book checkout/return records | `id`, `user_id`, `book_id`, `issued_at`, `due_date`, `returned_at`, `created_at`, `updated_at` | `N:1` to `users`, `N:1` to `books` |

### Important Constraints and Indexes

- `authors`: case-insensitive unique name (`ux_authors_name_lower`), non-empty name requirement, biography length limit.
- `books`: no future publication dates, no negative copy counts.
- `book_loans`: valid issue/return date checks, partial indexes for open loans.
- `refresh_sessions`: unique `token_hash`, `expires_at > created_at` check, partial index for active sessions.

---

## ⚙️ Configuration

Main environment files:

- `.env.example` — local run.
- `deployment/.env.example` — Docker Compose / server deployment.

Key variable groups:

| Group | Examples | Purpose |
|--------|---------|------------|
| API | `API_HOST`, `API_PORT`, `API_DEBUG` | FastAPI/Uvicorn settings |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Authentication and token lifetimes |
| DB | `DB_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` | PostgreSQL connection and pools |
| APP/LOG | `APP_ENV`, `LOG_LEVEL`, `LOG_TO_FILE` | Environment mode and logging |

---

## 🧪 Quality and Testing

```bash
# Unit tests
make test

# Lint + format + type-check
make check
```

Tools used:

- `pytest`, `pytest-asyncio`
- `ruff`
- `basedpyright`
