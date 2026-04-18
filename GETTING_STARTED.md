# 🚀 Быстрый старт: Система «Engels»

Это руководство поможет вам запустить систему Engels для локальной разработки.

## 📋 Требования

- **Docker** ≥ 24.0 и **Docker Compose** ≥ 2.20
- **Python** ≥ 3.11 (для локальной разработки)
- **Node.js** ≥ 18 (опционально, для frontend)
- **Git** ≥ 2.40
- Минимум **8 GB RAM** (рекомендуется 16 GB для работы с LLM)
- **GPU** (опционально, для ускорения Ollama)

## 🔧 Установка

### 1. Клонируйте репозиторий

```bash
git clone <repository-url>
cd engels
```

### 2. Настройте переменные окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` при необходимости:
- Измените пароли для базы данных
- Настройте порты сервисов
- Укажите пути к API токенам

### 3. Запустите инфраструктуру

```bash
# Запуск всех базовых сервисов (PostgreSQL, Redis, Ollama)
make docker-up

# Проверка статуса
docker compose ps
```

### 4. Установите зависимости для разработки

```bash
# Python зависимости
make install

# Frontend зависимости (опционально)
cd frontend && npm install
```

## ✅ Проверка работоспособности

### PostgreSQL + pgvector

```bash
docker compose exec postgres psql -U engels -d engels -c "SELECT * FROM sources LIMIT 1;"
```

### Redis

```bash
docker compose exec redis redis-cli ping
# Должен вернуть: PONG
```

### Ollama

```bash
curl http://localhost:11434/api/tags
```

Загрузка модели (если еще не загружена):

```bash
docker compose exec ollama ollama pull qwen2.5:7b
```

## 🏃 Запуск разработки

### Backend

```bash
# В одном терминале
make dev
```

Backend будет доступен на `http://localhost:8000`

### Celery Worker

```bash
# В другом терминале
make celery
```

### Frontend (опционально)

```bash
cd frontend
npm run dev
```

Frontend будет доступен на `http://localhost:3000`

### Strapi CMS (Фаза 3)

```bash
# Запуск с профилем CMS
docker compose --profile cms up -d strapi
```

Strapi будет доступен на `http://localhost:1337`

## 🧪 Тестирование

```bash
# Запуск всех тестов
make test

# Запуск с покрытием
make coverage

# Запуск конкретного теста
pytest tests/test_schemas.py -v
```

## 📊 Мониторинг

### Логи сервисов

```bash
# Все логи
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f ollama
```

### Состояние БД

```bash
docker compose exec postgres psql -U engels -d engels
```

Полезные запросы:

```sql
-- Количество документов
SELECT COUNT(*) FROM sources;

-- Количество сущностей
SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;

-- Последние изменения
SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT 10;
```

## 🛑 Остановка

```bash
# Остановка всех сервисов
make docker-down

# Остановка с удалением томов (данные будут потеряны!)
docker compose down -v
```

## ⚠️ Частые проблемы

### Ollama не запускается

Проверьте, что порт 11434 свободен:

```bash
lsof -i :11434
```

Если используется GPU, убедитесь, что установлены драйверы NVIDIA и `nvidia-container-toolkit`.

### Ошибки подключения к БД

Убедитесь, что PostgreSQL полностью запустился:

```bash
docker compose logs postgres | grep "ready to accept connections"
```

### Проблемы с памятью

Ollama может требовать много памяти. Уменьшите `OLLAMA_NUM_PARALLEL` в `.env`:

```env
OLLAMA_NUM_PARALLEL=1
```

Или увеличьте лимиты в `docker-compose.yml`.

## 📚 Следующие шаги

1. Изучите [ARCHITECTURE.md](./ARCHITECTURE.md) для понимания архитектуры
2. Посмотрите [ROADMAP.md](./ROADMAP.md) для плана развития
3. Начните с добавления тестового документа через API
4. Исследуйте граф знаний через Strapi CMS (Фаза 3)

## 🆘 Поддержка

- Документация: [README.md](./README.md)
- Архитектура: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Roadmap: [ROADMAP.md](./ROADMAP.md)
- Issues: GitHub Issues

---

*Последнее обновление: 2025-04-18*
