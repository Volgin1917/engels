# 🤝 Вклад в проект «Engels»

Спасибо за интерес к проекту! Это руководство описывает процесс внесения изменений.

## 📜 Принципы разработки

1. **Локальный инференс** — все LLM работают локально через Ollama
2. **Верифицируемость** — каждое утверждение имеет ссылку на источник
3. **DLP-анонимизация** — чувствительные данные удаляются до обработки
4. **Замкнутый контур** — система работает без внешних API

## 🔄 Процесс работы с кодом

### 1. Форк и клонирование

```bash
git clone https://github.com/<your-username>/engels.git
cd engels
git remote add upstream https://github.com/original/engels.git
```

### 2. Создание ветки

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

**Именование веток:**
- `feature/` — новая функциональность
- `bugfix/` — исправление ошибок
- `docs/` — документация
- `refactor/` — рефакторинг
- `test/` — тесты

### 3. Разработка

#### Требования к коду

- **Python**: следуем PEP 8, используем type hints
- **TypeScript**: строгий режим, интерфейс для всех props
- **Коммиты**: атомарные, с понятными сообщениями

#### Запуск линтеров перед коммитом

```bash
make lint
make format
```

#### Написание тестов

```bash
# Новый тест должен покрывать:
# - Обычный случай (happy path)
# - Граничные условия
# - Ошибочные ситуации

pytest tests/test_your_feature.py -v
```

### 4. Коммиты

Используем [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавить извлечение сущностей из текста
fix: исправить утечку памяти в Celery worker
docs: обновить README.md
refactor: упростить логику векторизации
test: добавить тесты для schemas.py
```

### 5. Pull Request

1. Обновите ветку:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. Запустите тесты:
   ```bash
   make test
   ```

3. Создайте PR на GitHub:
   - Заголовок: используйте Conventional Commits
   - Описание: что сделано, почему, как тестировать
   - Скриншоты: для UI изменений
   - Closes: ссылка на issue

### 6. Code Review

- Минимум 1 аппрув от мейнтейнера
- Все комментарии должны бытьresolved
- CI/CD должен пройти успешно

## 📝 Стандарты кода

### Python

```python
# ✅ Хорошо
from typing import Optional
from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    entity_type: str
    confidence: float = 0.0
    
    def is_verified(self) -> bool:
        return self.confidence > 0.8


# ❌ Избегайте
def process(data):  # Нет типов
    x = data['value']  # Магические ключи
    return x * 2
```

### TypeScript/React

```tsx
// ✅ Хорошо
interface EntityProps {
  id: number;
  name: string;
  onEdit?: (id: number) => void;
}

export const EntityCard: React.FC<EntityProps> = ({ 
  id, 
  name, 
  onEdit 
}) => {
  return (
    <div onClick={() => onEdit?.(id)}>
      {name}
    </div>
  );
};

// ❌ Избегайте
function EntityCard(props) {  // Нет типов
  return <div>{props.name}</div>;  // any props
}
```

### SQL

```sql
-- ✅ Хорошо
SELECT 
    e.id,
    e.name,
    e.entity_type,
    COUNT(r.id) AS relation_count
FROM entities e
LEFT JOIN relations r ON e.id = r.subject_id
WHERE e.category = 'person'
GROUP BY e.id, e.name, e.entity_type
ORDER BY relation_count DESC
LIMIT 100;

-- Используйте параметризованные запросы!
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
make test

# С покрытием
make coverage

# Конкретный файл
pytest tests/test_schemas.py -v

# С отладкой
pytest tests/ -s --pdb
```

### Покрытие кодом

Целевое покрытие: **≥80%**

Новый код должен иметь тесты. Исключения:
- Конфигурационные файлы
- Документация
- Scripts для одноразового запуска

## 📚 Документация

### Обновление документации

Если вы меняете API или поведение:

1. Обновите docstring в коде
2. Добавьте пример использования
3. Обновите README.md или ARCHITECTURE.md при необходимости

### Формат docstring

```python
def extract_entities(text: str, model: str = "qwen2.5:7b") -> list[Entity]:
    """
    Извлекает сущности из текста с помощью LLM.
    
    Args:
        text: Исходный текст для анализа
        model: Название модели Ollama (по умолчанию: qwen2.5:7b)
    
    Returns:
        Список извлеченных сущностей с метаданными
    
    Raises:
        OllamaConnectionError: Если Ollama недоступен
        ValueError: Если текст пустой
    
    Example:
        >>> entities = extract_entities("Маркс написал Капитал")
        >>> len(entities)
        2
    """
```

## 🐛 Сообщение об ошибках

Создайте issue с шаблоном:

```markdown
**Описание**
Краткое описание проблемы

**Воспроизведение**
Шаги:
1. Запустить...
2. Отправить запрос...
3. Увидеть ошибку...

**Ожидаемое поведение**
Что должно было произойти

**Логи**
```
<вставьте логи>
```

**Окружение**
- OS: Ubuntu 22.04
- Docker: 24.0
- Python: 3.11
```

## 💡 Предложения по улучшению

Обсуждайте крупные изменения в Discussions перед началом работы.

## 👥 Контакты

- Вопросы: GitHub Discussions
- Баги: GitHub Issues
- Безопасность: security@engels.local (не публикуйте уязвимости в issues!)

---

*Спасибо за ваш вклад в развитие системы «Engels»!*
