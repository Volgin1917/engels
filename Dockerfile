# syntax=docker/dockerfile:1

# ==========================================
# Этап 1: Builder (Сборка зависимостей)
# ==========================================
FROM python:3.11-slim as builder

# Установка системных зависимостей для компиляции пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только файлы зависимостей сначала (кэширование слоя)
COPY pyproject.toml ./

# Создаем виртуальное окружение и устанавливаем зависимости
# --prefix позволяет установить пакеты в конкретную папку без активации venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем все зависимости (включая тяжелые для сборки, если они есть в pyproject.toml)
# В продакшене мы будем использовать только то, что нужно для запуска
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# ==========================================
# Этап 2: Runtime (Минимальный образ)
# ==========================================
FROM python:3.11-slim as runtime

# Метаданные
LABEL maintainer="your-team@example.com"
LABEL version="1.0"
LABEL description="Knowledge Graph Backend Service"

# Создание не-рутового пользователя для безопасности
RUN useradd --create-home --shell /bin/bash appuser

# Установка только рантайм-зависимостей (без компиляторов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Копируем виртуальное окружение из билдера
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем исходный код
COPY . .

# Смена владельца файлов на не-рутового пользователя
RUN chown -R appuser:appuser /app

# Переключение на не-рутового пользователя
USER appuser

# Экспозиция порта (настраивается через переменные окружения в runtime)
EXPOSE 8000

# Healthcheck для оркестраторов
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Точка входа
# Используем exec form для правильной передачи сигналов SIGTERM/SIGINT
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
