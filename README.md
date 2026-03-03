<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![Poetry](https://img.shields.io/badge/poetry-package%20manager-purple)](https://python-poetry.org/) [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-brightgreen)](https://github.com/astral-sh/ruff) [![Type checked: mypy](https://img.shields.io/badge/types-mypy-blue)](https://github.com/python/mypy) [![Docker](https://img.shields.io/badge/docker-ready-2496ED)](https://www.docker.com/) [![Pydantic](https://img.shields.io/badge/pydantic-v2-red)](https://docs.pydantic.dev/) [![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-2.0-orange)](https://www.sqlalchemy.org/) [![Structlog](https://img.shields.io/badge/structlog-24.0-lightgrey)](https://www.structlog.org/) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://pre-commit.com/) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

</div>

<div align="center">
  <a href="#english">🇬🇧 English</a> | <a href="#russian">🇷🇺 Русский</a>
</div>
<br>

---

<a id="english"></a>
<div align="center">

# 📄 Document Crawler

A production-ready document crawler with full-text search capabilities.
Extracts text from various formats, handles nested archives, and provides powerful FTS.
</div>

---

## 📋 Table of Contents
- [Features](#features-english)
- [Supported Formats](#supported-formats-english)
- [Quick Start](#quick-start-english)
- [Project Structure](#project-structure-english)
- [Configuration](#configuration-english)
- [Usage](#usage-english)
- [Architecture](#architecture-english)
- [Development](#development-english)
- [License](#license-english)

---

<a id="features-english"></a>
## ✨ Features

- **Deep Crawling**: Recursive directory traversal with hidden file support
- **Archive Extraction**: Automatic unpacking of ZIP, RAR, 7z (including nested archives up to 3 levels)
- **Multi-format Support**: Text extraction from 10+ document formats
- **Full-Text Search**: SQLite FTS5 with automatic indexing and triggers
- **Dual Output**: Results saved to both SQLite (for search) and CSV (for analysis)
- **Production Ready**:
  - Full type hints with mypy --strict
  - Structured logging with structlog
  - Clean Architecture with clear separation of concerns
  - Docker support

---

<a id="supported-formats-english"></a>
## 📑 Supported Formats

| Format | Status | Library/Tool | Notes |
|--------|--------|--------------|-------|
| PDF | ✅ | PyPDF2 | Text extraction from all pages |
| DOCX | ✅ | python-docx | Paragraphs and tables |
| DOC | ⚠️ | antiword/catdoc | Not tested. Not applicable in Docker. Requires external utilities* |
| XLSX | ✅ | openpyxl | All sheets and cells |
| XLS | ✅ | xlrd | Legacy Excel format |
| TXT | ✅ | built-in | Auto-encoding detection |
| MD | ✅ | TextParser | Markdown as plain text |
| JSON | ✅ | TextParser | JSON as plain text |
| XML | ✅ | TextParser | XML as plain text |
| HTML | ✅ | TextParser | HTML as plain text |
| ZIP | ✅ | patool | Nested archives supported |
| RAR | ⚠️ | patool + unrar | Requires external unrar* or use via docker |
| 7Z | ⚠️ | patool + p7zip | Requires external p7zip* or use via docker |

*\*External utilities need to be installed separately in the system (see [External Dependencies](#external-dependencies-english))*.

---

<a id="quick-start-english"></a>
## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Your files to crawl (place them in `data/storage/`)

### Installation

```bash
# Clone the repository
git clone https://github.com/script-logic/document-crawler.git
cd document-crawler

# Create .env file from example
cp .env.example .env

# Install with poetry
poetry install
```

### Basic Usage

```bash
# Generate sample test files (optional)
poetry run python run_crawler.py generate-samples

# Crawl storage directory
poetry run python run_crawler.py crawl

# Search indexed documents
poetry run python run_crawler.py search "your query"
```

---

<a id="project-structure-english"></a>
## 📁 Project Structure

```
├── app/                                # Main application package
│   ├── application/                    # Use cases (business logic)
│   │   └── use_cases/
│   │       ├── crawl.py                # Crawling orchestration
│   │       └── search.py               # Search orchestration
│   ├── config/                         # Configuration
│   │   └── config.py                   # Pydantic settings
│   ├── domain/                         # Domain models
│   │   ├── entities/                   # Document entity
│   │   └── value_objects/              # FileHash value object
│   ├── infrastructure/                 # External concerns
│   │   ├── crawler/                    # File scanning & archives
│   │   ├── database/                   # SQLAlchemy models & repository
│   │   ├── logger/                     # Structured logging
│   │   └── parsers/                    # Document parsers (PDF, DOCX, etc.)
│   └── utils/                          # Helpers (Singleton)
├── data/                               # Storage and output
│   ├── storage/                        # Place your files here
│   └── output/                         # Generated CSV files
├── tests/                              # Test suite
├── .env.example                        # Example environment
├── docker-compose.yml                  # Docker setup
├── pyproject.toml                      # Project metadata
└── run_crawler.py                      # Entry point
```

---

<a id="configuration-english"></a>
## ⚙️ Configuration

Configure via `.env` file (copy from `.env.example`):

```env
# Logging
LOGGER__APP_NAME=Document Crawler
LOGGER__DEBUG=true
LOGGER__LOG_LEVEL=INFO
LOGGER__ENABLE_FILE_LOGGING=false
LOGGER__LOGS_DIR=logs

# Storage paths
CRAWLER__STORAGE_PATH=data/storage
CRAWLER__OUTPUT_CSV_PATH=data/output/crawled_files.csv

# Crawler settings
CRAWLER__MAX_FILE_SIZE_MB=100
CRAWLER__SKIP_HIDDEN=true
CRAWLER__EXTRACT_ARCHIVES=true
CRAWLER__MAX_ARCHIVE_DEPTH=3

# Supported extensions
CRAWLER__EXTRACT_TEXT_FROM=["pdf", "docx", "xlsx", "doc", "xls", "txt", "md", "json", "xml", "html"]
CRAWLER__ARCHIVE_EXTENSIONS=["zip", "rar", "7z"]

# Database
DATABASE__PATH=db/crawler.db
DATABASE__FTS_ENABLED=true
```

---

<a id="usage-english"></a>
## 🎯 Usage

### Commands

```bash
# Crawl storage directory
python run_crawler.py crawl [OPTIONS]

Options:
  --storage PATH     Path to storage directory (default: data/storage)
  --output PATH      Path to output CSV (default: data/output/crawled_files.csv)
  --limit N          Maximum number of files to process
  --no-archives      Don't extract archives

# Search indexed documents
python run_crawler.py search QUERY [OPTIONS]

Options:
  --limit N          Maximum results to return (default: 20)
  --type TYPE        Filter by document type (pdf, docx, xlsx, txt)

# Show database statistics
python run_crawler.py stats

# Generate test files
python run_crawler.py generate-samples [OPTIONS]

Options:
  --output PATH      Output directory (default: tests/fixtures/samples)
  --count N          Number of samples per type (default: 5)
```

### Examples

```bash
# Full crawl
poetry run python run_crawler.py crawl

# Crawl with limit (for testing)
poetry run python run_crawler.py crawl --limit 100

# Search with filters
poetry run python run_crawler.py search "financial report" --type pdf --limit 10

# Complex FTS query (phrases, NEAR operator)
poetry run python run_crawler.py search '"tax planning" NEAR/5 client'

# Database stats
poetry run python run_crawler.py stats

# Generate 10 test files
poetry run python run_crawler.py generate-samples --count 10
```

---

<a id="architecture-english"></a>
## 🏗 Architecture

- **Domain Layer**: Business logic, no external dependencies (except pydantic)
- **Application Layer**: Orchestrates use cases, depends on abstractions
- **Infrastructure Layer**: Implements interfaces, handles external concerns
- **Dependency Injection**: All components receive their dependencies
- **Repository Pattern**: Abstracts data storage
- **Factory Pattern**: Creates appropriate parsers based on file type

---

<a id="external-dependencies-english"></a>
## 🔧 External Dependencies

Some formats require system-level utilities:

| Format | Required Tool | Installation |
|--------|--------------|--------------|
| **RAR archives** | `unrar` | **Windows**: Install WinRAR or 7-Zip<br>**Linux**: `sudo apt-get install unrar`<br>**macOS**: `brew install unrar` |
| **7Z archives** | `p7zip` | **Windows**: Install 7-Zip<br>**Linux**: `sudo apt-get install p7zip-full`<br>**macOS**: `brew install p7zip` |
| **DOC files** | `antiword` or `catdoc` | **Windows**: https://github.com/rsdoiel/antiword<br>**Linux**: `sudo apt-get install antiword`<br>**macOS**: `brew install antiword` |

> **Note**: These are external executables, not Python packages. They must be installed in your system PATH. Please note: these external tools may not be available on your system even after following the installation instructions above.

---

<a id="development-english"></a>
## 🛠 Development

### Setup

```bash
# Install with dev dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

### Available Make Commands

```bash
make run-crawl            # Run crawler
make run-search QUERY=... # Search documents
make run-stats            # Show database stats
make run-generate-samples # Generate test files
make up                   # Start Docker container
make down                 # Stop Docker container
make lint                 # Run ruff and mypy
make format               # Format code with ruff
make clean                # Clean cache files
```

### Code Quality

- **Ruff**: Fast Python linter (replaces flake8, isort)
- **mypy**: Strict type checking with `--strict`
- **pre-commit**: Automated checks before commits

### Docker

```bash
# Build and run
docker-compose up

# Run with custom command
docker-compose run --rm crawler python run_crawler.py search "query"

# Rebuild
docker-compose build --no-cache
```

---

<a id="license-english"></a>
## 📝 License

MIT License - feel free to use and modify.

---

<br>
<hr>
<br>

<a id="russian"></a>

<div align="center">
  <a href="#english">🇬🇧 English</a> | <a href="#russian">🇷🇺 Русский</a>
</div>

<div align="center">

# 📄 Краулер документов

Продакшен-реди краулер документов с полнотекстовым поиском.
Извлекает текст из различных форматов, обрабатывает вложенные архивы и предоставляет мощный FTS.
</div>

---

## 📋 Содержание
- [Возможности](#возможности-russian)
- [Поддерживаемые форматы](#поддерживаемые-форматы-russian)
- [Быстрый старт](#быстрый-старт-russian)
- [Структура проекта](#структура-проекта-russian)
- [Конфигурация](#конфигурация-russian)
- [Использование](#использование-russian)
- [Архитектура](#архитектура-russian)
- [Разработка](#разработка-russian)
- [Лицензия](#лицензия-russian)

---

<a id="возможности-russian"></a>
## ✨ Возможности

- **Глубокий обход**: Рекурсивный обход директорий с поддержкой скрытых файлов
- **Извлечение из архивов**: Автоматическая распаковка ZIP, RAR, 7z (включая вложенные архивы до 3 уровней)
- **Мультиформатность**: Извлечение текста из 10+ форматов документов
- **Полнотекстовый поиск**: SQLite FTS5 с автоматическим индексированием и триггерами
- **Двойной вывод**: Сохранение в SQLite (для поиска) и CSV (для анализа)
- **Готов к продакшену**:
  - Полная типизация (mypy --strict)
  - Структурированное логирование (structlog)
  - Чистая архитектура
  - Поддержка Docker

---

<a id="поддерживаемые-форматы-russian"></a>
## 📑 Поддерживаемые форматы

| Формат | Статус | Библиотека/Утилита | Примечания |
|--------|--------|-------------------|------------|
| PDF | ✅ | PyPDF2 | Извлечение текста со всех страниц |
| DOCX | ✅ | python-docx | Параграфы и таблицы |
| DOC | ⚠️ | antiword/catdoc | Не протестировано. Не используется в docker. Требует внешние утилиты* |
| XLSX | ✅ | openpyxl | Все листы и ячейки |
| XLS | ✅ | xlrd | Старый формат Excel |
| TXT | ✅ | встроенный | Автоопределение кодировки |
| MD | ✅ | TextParser | Markdown как plain text |
| JSON | ✅ | TextParser | JSON как plain text |
| XML | ✅ | TextParser | XML как plain text |
| HTML | ✅ | TextParser | HTML как plain text |
| ZIP | ✅ | patool | Поддержка вложенных архивов |
| RAR | ⚠️ | patool + unrar | Требует внешний unrar* или используйте docker |
| 7Z | ⚠️ | patool + p7zip | Требует внешний p7zip* или используйте docker |

*\*Внешние утилиты устанавливаются отдельно в систему (см. [Внешние зависимости](#внешние-зависимости-russian))*.

---

<a id="быстрый-старт-russian"></a>
## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Poetry
- Ваши файлы для индексации (поместите в `data/storage/`)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/script-logic/document-crawler.git
cd document-crawler

# Создать .env файл из примера
cp .env.example .env

# Установка с poetry
poetry install
```

### Базовое использование

```bash
# Сгенерировать тестовые файлы (опционально)
poetry run python run_crawler.py generate-samples

# Запустить краулер
poetry run python run_crawler.py crawl

# Поиск по индексированным документам
poetry run python run_crawler.py search "ваш запрос"
```

---

<a id="структура-проекта-russian"></a>
## 📁 Структура проекта

```
├── app/                                # Основной пакет приложения
│   ├── application/                    # Use cases (бизнес-логика)
│   │   └── use_cases/
│   │       ├── crawl.py                # Оркестрация краулинга
│   │       └── search.py               # Оркестрация поиска
│   ├── config/                         # Конфигурация
│   │   └── config.py                   # Pydantic настройки
│   ├── domain/                         # Доменные модели
│   │   ├── entities/                   # Сущность Document
│   │   └── value_objects/              # Value object FileHash
│   ├── infrastructure/                 # Внешние зависимости
│   │   ├── crawler/                    # Сканирование и архивы
│   │   ├── database/                   # SQLAlchemy модели и репозиторий
│   │   ├── logger/                     # Структурированное логирование
│   │   └── parsers/                    # Парсеры документов
│   └── utils/                          # Вспомогательные утилиты
├── data/                               # Хранилище и вывод
│   ├── storage/                        # Сюда класть файлы
│   └── output/                         # Сгенерированные CSV
├── tests/                              # Тесты
├── .env.example                        # Пример .env
├── docker-compose.yml                  # Docker настройки
├── pyproject.toml                      # Метаданные проекта
└── run_crawler.py                      # Точка входа
```

---

<a id="конфигурация-russian"></a>
## ⚙️ Конфигурация

Настройка через `.env` файл (скопируйте из `.env.example`):

```env
# Логирование
LOGGER__APP_NAME=Document Crawler
LOGGER__DEBUG=true
LOGGER__LOG_LEVEL=INFO
LOGGER__ENABLE_FILE_LOGGING=false
LOGGER__LOGS_DIR=logs

# Пути к данным
CRAWLER__STORAGE_PATH=data/storage
CRAWLER__OUTPUT_CSV_PATH=data/output/crawled_files.csv

# Настройки краулера
CRAWLER__MAX_FILE_SIZE_MB=100
CRAWLER__SKIP_HIDDEN=true
CRAWLER__EXTRACT_ARCHIVES=true
CRAWLER__MAX_ARCHIVE_DEPTH=3

# Поддерживаемые расширения
CRAWLER__EXTRACT_TEXT_FROM=["pdf", "docx", "xlsx", "doc", "xls", "txt", "md", "json", "xml", "html"]
CRAWLER__ARCHIVE_EXTENSIONS=["zip", "rar", "7z"]

# База данных
DATABASE__PATH=db/crawler.db
DATABASE__FTS_ENABLED=true
```

---

<a id="использование-russian"></a>
## 🎯 Использование

### Команды

```bash
# Краулинг директории
python run_crawler.py crawl [ОПЦИИ]

Опции:
  --storage PATH     Путь к директории с файлами (по умолч.: data/storage)
  --output PATH      Путь к выходному CSV (по умолч.: data/output/crawled_files.csv)
  --limit N          Максимальное количество файлов
  --no-archives      Не обрабатывать архивы

# Поиск по индексированным документам
python run_crawler.py search ЗАПРОС [ОПЦИИ]

Опции:
  --limit N          Максимум результатов (по умолч.: 20)
  --type TYPE        Фильтр по типу (pdf, docx, xlsx, txt)

# Статистика БД
python run_crawler.py stats

# Генерация тестовых файлов
python run_crawler.py generate-samples [ОПЦИИ]

Опции:
  --output PATH      Директория для сохранения (по умолч.: tests/fixtures/samples)
  --count N          Количество файлов каждого типа (по умолч.: 5)
```

### Примеры

```bash
# Полный краулинг
poetry run python run_crawler.py crawl

# Краулинг с лимитом (для тестирования)
poetry run python run_crawler.py crawl --limit 100

# Поиск с фильтрами
poetry run python run_crawler.py search "финансовый отчет" --type pdf --limit 10

# Сложный FTS запрос (фразы, NEAR оператор)
poetry run python run_crawler.py search '"налоговое планирование" NEAR/5 клиент'

# Статистика БД
poetry run python run_crawler.py stats

# Генерация 10 тестовых файлов
poetry run python run_crawler.py generate-samples --count 10
```

---

<a id="архитектура-russian"></a>
## 🏗 Архитектура

- **Доменный слой**: Бизнес-логика, нет внешних зависимостей (кроме pydantic для удобства валидации)
- **Слой приложения**: Оркестрирует use cases, зависит от абстракций
- **Инфраструктурный слой**: Реализует интерфейсы, работает с внешними системами
- **Внедрение зависимостей**: Все компоненты получают зависимости через конструктор
- **Репозиторий**: Абстрагирует хранение данных
- **Фабрика**: Создает парсеры на основе типа файла

---

<a id="внешние-зависимости-russian"></a>
## 🔧 Внешние зависимости

Некоторые форматы требуют системных утилит:

| Формат | Требуемая утилита | Установка |
|--------|------------------|-----------|
| **RAR архивы** | `unrar` | **Windows**: Установите WinRAR или 7-Zip<br>**Linux**: `sudo apt-get install unrar`<br>**macOS**: `brew install unrar` |
| **7Z архивы** | `p7zip` | **Windows**: Установите 7-Zip<br>**Linux**: `sudo apt-get install p7zip-full`<br>**macOS**: `brew install p7zip` |
| **DOC файлы** | `antiword` или `catdoc` | **Windows**: https://github.com/rsdoiel/antiword<br>**Linux**: `sudo apt-get install antiword`<br>**macOS**: `brew install antiword` |

> **Важно**: Это внешние исполняемые файлы, а не Python-пакеты. Они должны быть установлены в системе и доступны в PATH. Примечание: эти внешние инструменты могут отсутствовать в вашей системе или быть недоступны, даже если вы следовали инструкциям по установке, приведенным выше.

---

<a id="разработка-russian"></a>
## 🛠 Разработка

### Настройка

```bash
# Установка с dev зависимостями
poetry install --with dev

# Установка pre-commit хуков
pre-commit install
```

### Доступные Make команды

```bash
make run-crawl            # Запуск краулера
make run-search QUERY=... # Поиск документов
make run-stats            # Статистика БД
make run-generate-samples # Генерация тестовых файлов
make up                   # Запуск Docker контейнера
make down                 # Остановка Docker
make lint                 # Запуск ruff и mypy
make format               # Форматирование кода
make clean                # Очистка кеша
```

### Качество кода

- **Ruff**: Быстрый линтер Python (заменяет flake8, isort)
- **mypy**: Строгая проверка типов с `--strict`
- **pre-commit**: Автоматические проверки перед коммитами
- **pytest**: Набор тестов с покрытием

### Docker

```bash
# Сборка и запуск
docker-compose up

# Запуск с произвольной командой
docker-compose run --rm crawler python run_crawler.py search "запрос"

# Пересборка
docker-compose build --no-cache
```

---

<a id="лицензия-russian"></a>
## 📝 Лицензия

MIT License - свободно используйте и модифицируйте.

---
