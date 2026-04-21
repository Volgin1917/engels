# Strapi CMS с поддержкой кастомных плагинов
# Сборка из исходников для возможности установки плагинов
# Архитектура: multi-stage build для оптимизации размера образа

FROM node:18-alpine AS base

# Установка системных зависимостей для сборки
RUN apk add --no-cache python3 make g++ vips-dev

WORKDIR /opt/app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./

# Устанавливаем все зависимости (включая dev для сборки)
RUN npm install

# Копируем весь проект Strapi
COPY . .

# Собираем админ-панель
RUN npm run build

# Финальный образ
FROM node:18-alpine

WORKDIR /opt/app

# Копируем собранный проект и зависимости
COPY --from=base /opt/app/node_modules ./node_modules
COPY --from=base /opt/app/build ./build
COPY --from=base /opt/app/dist ./dist
COPY --from=base /opt/app/package*.json ./
COPY . .

# Открываем порт
EXPOSE 1337

# Команда запуска
CMD ["npm", "run", "develop"]
