# Lenta Parser

## Описание парсеров

### 1. lenta_cookies

**Назначение:** Создание и сохранение cookies для обхода антибот-защиты. 

**Как работает:**
- Использует Camoufox для эмуляции реального браузера
- Посещает главную страницу сайта через прокси
- Сохраняет полученные cookies в базу данных
- Удаляет старые записи перед запуском

**Примечания:**
- Нужно использовать статичные прокси, так как куки привязываются к ip адресам.
- В данном проекте используются прокси с авторизацией http://user:password@ip:port
- Для использования стандартого файла прокси, создайте файл list_proxies.txt в папке files.

**Запуск:**

```bash
# Базовый запуск
scrapy crawl lenta_cookies

# С указанием файла с прокси
scrapy crawl lenta_cookies -a proxy_file="/path"
```

**Параметры:**
- `proxy_file` - путь к файлу со списком прокси (по умолчанию: `files/list_proxies.txt`).

---

### 2. lenta_links

**Назначение:** Сбор ссылок на категории каталога.

**Как работает:**
- Парсит страницу каталога
- Извлекает ссылки на все категории
- Сохраняет данные в Redis для последующего использования

**Запуск:**

```bash
# Базовый запуск
scrapy crawl lenta_cookies

С указанием прокси
scrapy crawl lenta_links -a PROXY="http://user:password@ip:port"
```

**Параметры:**
- `PROXY` - прокси

---

### 3. lenta_catalog

**Назначение:** Парсинг каталога товаров с получением информации о ценах и наличии.

**Как работает:**
- Устанавливает адрес магазина
- Запрашивает данные через API Lenta
- Использует scrapy-impersonate для эмуляции браузера Firefox
- Автоматически меняет cookies/headers при ошибках 403/401
- Сохраняет данные о товарах в базу данных

**Примечание:** Для работы парсера необходимо сначала запустить `lenta_cookies` для создания cookies и `lenta_links` для сбора ссылок на категории.

**Запуск:**

```bash
# Базовый запуск
scrapy crawl lenta_catalog

# С указанием адреса магазина
scrapy crawl lenta_catalog -a address="Самара, Аэродромная ул., 47А, ТЦ Аврора-молл"
```

**Параметры:**
- `address` - полный адрес магазина для получения storeId (опционально)

- **Примечание:** Прокси указывать не нужно, так как они уже есть в БД с cookies.
- **Примечание:** В настройках установлены настройки, ограничивающие нагрузку.

```
DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS = 1
```

---

## 📦 Требования

- Python
- PostgreSQL
- Redis
- Docker (для Camoufox)

## 🚀 Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd parse_project
```

### 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# PostgreSQL
HOSTNAME_POSTGRESQL=localhost
USERNAME_POSTGRESQL=your_username
PASSWORD_POSTGRESQL=your_password
DATABASE_POSTGRESQL=your_database
PORT_POSTGRESQL=5432

# Redis
PORT_REDIS=6379
```

### 5. Создание таблиц в базе данных

Выполните SQL-скрипт для создания необходимых таблиц:

```sql
-- Таблица для хранения cookies и headers
CREATE TABLE cookies_headers (
    id SERIAL PRIMARY KEY,
    url TEXT,
    cookies JSONB,
    headers JSONB,
    proxy TEXT,
    store_id INTEGER,
    meta JSONB,
    spider TEXT,
    type_proxy TEXT,
    provider_proxy TEXT,
    date_added TIMESTAMP WITH TIME ZONE,
    time_request FLOAT
);

-- Таблица для хранения товаров
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    title TEXT,
    sku BIGINT,
    price NUMERIC,
    price_card NUMERIC,
    url TEXT,
    img_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 6. Запуск Camoufox Docker сервиса

```bash
cd camoufox_docker
docker build -t camoufox-service .
docker run -p 8000:8000 camoufox-service
```

---

### 7. Создание папки с логами.
```bash
mkdir -p files/logs
```

### 8. Создание стандартного файла с прокси.
```bash
touch files/list_proxies.txt
```

## 📁 Структура проекта

```
parse_project/
├── scrapy_root/
│   ├── spiders/
│   │   └── lenta/
│   │       ├── __init__.py
│   │       ├── headers.py      # Генерация headers для API запросов
│   │       └── spider.py       # Основные пауки (cookies, links, catalog)
│   ├── handlers/
│   │   ├── docker_handler.py           # Handler для Camoufox
│   │   └── scrapy_impersonate/
│   │       ├── handler.py              # Handler для scrapy-impersonate
│   │       ├── middleware.py           # Middleware для impersonate
│   │       └── parser.py               # Парсер запросов
│   ├── middlewares.py                  # CookieProxyRetryMiddleware
│   ├── pipelines.py                    # Pipelines для обработки данных
│   ├── base_spiders.py                 # Базовый класс пауков
│   ├── items.py                        # Scrapy Items
│   ├── settings.py                     # Настройки Scrapy
│   └── services/
│       ├── database_service.py         # Сервис работы с PostgreSQL
│       ├── cookie_service.py           # Сервис работы с cookies
│       └── proxy_service.py            # Сервис работы с прокси
├── camoufox_docker/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py                       # Flask сервер для Camoufox
│   └── start.sh
├── files/
│   ├── useragents.txt                  # Список User-Agent
│   └── list_proxies.txt                # Список прокси
├── requirements.txt
├── scrapy.cfg
└── .env                                # Переменные окружения
```

## 🔧 Компоненты системы

### Handlers

- **DockerDownloadHandler** - перенаправляет запросы в Camoufox Docker сервис для эмуляции браузера
- **ImpersonateDownloadHandler** - использует scrapy-impersonate для эмуляции браузера Firefox

### Middlewares

- **CookieProxyRetryMiddleware** - автоматически обрабатывает ошибки 403/401, меняя cookies и прокси

### Pipelines

- **CookiesHeadersPipeline** - сохраняет cookies и headers в базу данных
- **CatalogPipeline** - сохраняет данные о товарах в базу данных

### Services

- **DatabaseService** - управление соединениями с PostgreSQL
- **CookieService** - работа с cookies
- **ProxyService** - работа с прокси

## 🗄️ Таблицы базы данных

### cookies_headers

Хранит cookies и headers для обхода антибот-защиты.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Первичный ключ |
| url | TEXT | URL запроса |
| cookies | JSONB | Cookies |
| headers | JSONB | Headers |
| proxy | TEXT | Прокси-сервер |
| store_id | INTEGER | ID магазина |
| meta | JSONB | Дополнительные метаданные |
| spider | TEXT | Имя паука |
| type_proxy | TEXT | Тип прокси |
| provider_proxy | TEXT | Провайдер прокси |
| date_added | TIMESTAMP | Дата добавления |
| time_request | FLOAT | Время выполнения запроса |

### products

Хранит данные о товарах.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Первичный ключ |
| title | TEXT | Название товара |
| sku | BIGINT | SKU товара |
| price | NUMERIC | Обычная цена |
| price_card | NUMERIC | Цена по карте |
| url | TEXT | URL товара |
| img_url | TEXT | URL изображения |
| created_at | TIMESTAMP | Дата создания записи |


## Проблемы и способы их решения

### Ошибка 403 при парсинге

**Причина:** Cookies устарели или заблокированы.

**Решение:** Запустите `lenta_cookies` для создания новых cookies.

### Camoufox сервис недоступен

**Причина:** Docker контейнер не запущен.

**Решение:**
```bash
cd camoufox_docker
docker-compose up -d
```

### Ошибка подключения к PostgreSQL

**Причина:** Неверные настройки в `.env` файле.

**Решение:** Проверьте настройки подключения к базе данных.
