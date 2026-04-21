# Strapi CMS с поддержкой кастомных плагинов
FROM strapi/strapi:4.25.6

# Устанавливаем рабочую директорию
WORKDIR /opt/app

# Копируем package.json для установки зависимостей
COPY package*.json ./

# Устанавливаем зависимости (если есть кастомные)
RUN if [ -f "package.json" ]; then npm install --production; fi

# Монтируем исходники и плагины через volumes в docker-compose
# Эта сборка нужна только если вы добавляете системные зависимости или глобальные пакеты

# Пример установки системных зависимостей для специфичных плагинов
# RUN apk add --no-cache vips-dev fftw-dev gcc make cmake python3 py3-pip \
#     && rm -rf /var/cache/apk/*

# Открываем порт
EXPOSE 1337

# Команда запуска (стандартная для Strapi)
CMD ["npm", "run", "develop"]
