# Knowledge Graph - Infrastructure Setup

## Локальная разработка (Docker Compose)

### Быстрый старт

```bash
# Запуск всех сервисов
docker compose up -d

# Запуск с воркерами
docker compose --profile workers up -d

# Просмотр логов
docker compose logs -f backend

# Остановка
docker compose down
```

### Сервисы

- **Backend**: http://localhost:8000
- **Strapi CMS**: http://localhost:1337
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
STRAPI_API_TOKEN=your_token_here
APP_KEYS=key1,key2
API_TOKEN_SALT=your_salt
ADMIN_JWT_SECRET=your_secret
JWT_SECRET=your_jwt_secret
```

---

## Продакшн (Kubernetes)

### Требования

- Kubernetes кластер v1.25+
- kubectl настроен на ваш кластер
- Ingress Controller (nginx)
- cert-manager для SSL

### Развертывание

```bash
# Создание namespace и ресурсов
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Проверка статуса
kubectl get pods -n knowledge-graph
kubectl get services -n knowledge-graph
kubectl get ingress -n knowledge-graph
```

### Настройка секретов

Перед деплоем обновите секреты в `k8s/secret.yaml` или используйте внешний secrets manager:

```bash
# Пример создания secret через kubectl
kubectl create secret generic kg-secrets \
  --from-literal=DATABASE_PASSWORD='secure_password' \
  --from-literal=STRAPI_API_TOKEN='secure_token' \
  -n knowledge-graph
```

### Масштабирование

```bash
# Увеличение количества реплик backend
kubectl scale deployment kg-backend --replicas=5 -n knowledge-graph

# Увеличение количества воркеров
kubectl scale deployment kg-worker --replicas=4 -n knowledge-graph
```

### Мониторинг

```bash
# Логи backend
kubectl logs -f deployment/kg-backend -n knowledge-graph

# Логи воркера
kubectl logs -f deployment/kg-worker -n knowledge-graph

# Метрики
kubectl top pods -n knowledge-graph
```

---

## CI/CD (GitHub Actions)

Пайплайн автоматически:

1. **Тестирует** код при каждом PR/push
2. **Собирает** Docker образ при push в main/develop
3. **Деплоит** в Kubernetes при merge в main или создании тега

### Необходимые секреты GitHub

- `KUBE_CONFIG`: base64-encoded kubeconfig файл
- `GITHUB_TOKEN`: автоматически предоставляется GitHub

### Ручной триггер деплоя

```bash
# Создать тег для деплоя
git tag v1.0.0
git push origin v1.0.0
```

---

## Структура файлов

```
.
├── Dockerfile              # Образ приложения
├── docker-compose.yml      # Локальная разработка
├── .github/
│   └── workflows/
│       └── ci-cd.yml      # CI/CD пайплайн
└── k8s/
    ├── namespace.yaml          # Namespace
    ├── configmap.yaml          # Конфигурация
    ├── secret.yaml             # Секреты (шаблон)
    ├── backend-deployment.yaml # Deployment backend
    ├── backend-service.yaml    # Service backend
    ├── worker-deployment.yaml  # Deployment воркеров
    └── ingress.yaml            # Ingress规则
```

---

## Troubleshooting

### Backend не запускается

```bash
# Проверить логи
docker compose logs backend

# Проверить подключение к БД
docker compose exec backend python -c "from app.core.database import get_connection; print(get_connection())"
```

### Strapi недоступен

```bash
# Перезапустить Strapi
docker compose restart strapi

# Проверить миграции БД
docker compose exec strapi npm run build
```

### Проблемы с Kubernetes

```bash
# Описание пода
kubectl describe pod <pod-name> -n knowledge-graph

# Проверка событий
kubectl get events -n knowledge-graph --sort-by='.lastTimestamp'

# Debug под
kubectl run debug --image=busybox --rm -it --restart=Never -n knowledge-graph -- sh
```
