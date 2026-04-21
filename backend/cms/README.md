# Strapi CMS - сборка из исходников

## Архитектура

Этот каталог содержит проект Strapi CMS, который собирается в Docker-образ с поддержкой кастомных плагинов.

### Структура

```
backend/cms/
├── Dockerfile          # Multi-stage build для оптимизации размера
├── package.json        # Зависимости и скрипты
├── config/            # Конфигурация Strapi
├── src/               # Исходный код (типы контента, контроллеры)
└── plugins/           # Кастомные плагины
```

## Сборка образа

Образ собирается через `docker-compose`:

```bash
docker compose up --build strapi
```

### Процесс сборки

1. **Base stage**: Установка системных зависимостей (python3, make, g++, vips-dev)
2. **Install**: Установка npm зависимостей
3. **Build**: Компиляция админ-панели
4. **Final stage**: Копирование только необходимых файлов для уменьшения размера

## Добавление плагинов

### Вариант 1: Через package.json

Добавьте плагин в `package.json`:

```json
{
  "dependencies": {
    "@strapi/plugin-seo": "^1.0.0"
  }
}
```

Затем пересоберите образ.

### Вариант 2: Локальный плагин

1. Поместите плагин в папку `plugins/`
2. Обновите `package.json` для ссылки на локальный плагин
3. Пересоберите образ

## Конфигурация

Основные файлы конфигурации:

- `config/database.js` - подключение к PostgreSQL
- `config/server.js` - настройки сервера
- `config/plugins.js` - настройка плагинов (создаётся при необходимости)

## Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `DATABASE_CLIENT` | Тип БД | `postgres` |
| `DATABASE_HOST` | Хост БД | `db` |
| `DATABASE_PORT` | Порт БД | `5432` |
| `DATABASE_NAME` | Имя БД | `kg_strapi` |
| `DATABASE_USERNAME` | Пользователь БД | `postgres` |
| `DATABASE_PASSWORD` | Пароль БД | `postgres` |
| `APP_KEYS` | Ключи приложения | генерируются |
| `ADMIN_JWT_SECRET` | Секрет JWT админа | генерируется |
| `JWT_SECRET` | Секрет JWT | генерируется |

## Разработка

Для локальной разработки с hot-reload:

```bash
docker compose up strapi
```

Исходники монтируются через volumes в `docker-compose.yml`.

## Production

Для production сборки:

```bash
docker compose up --build
```

Multi-stage build обеспечивает минимальный размер финального образа.
