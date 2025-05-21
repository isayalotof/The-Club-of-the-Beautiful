# Веб-сайт для салона красоты

Веб-приложение для салона красоты с возможностью онлайн-записи на услуги.

## Функциональность

- Просмотр списка услуг с фильтрацией по категориям
- Детальная информация об услугах
- Онлайн-запись на выбранную услугу
- Личный кабинет пользователя для управления записями
- Административная панель для управления услугами и записями

## Технологии

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Аутентификация: JWT
- Контейнеризация: Docker, Docker Compose

## Запуск с использованием Docker

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/beauty-salon.git
cd beauty-salon
```

2. Создайте `.env` файл с переменными окружения (или используйте значения по умолчанию):
```
SECRET_KEY=your_secret_key_here
```

3. Запустите приложение с помощью Docker Compose:
```
docker compose up -d
```

4. Откройте в браузере:
   - Веб-сайт: http://localhost:8000
   - Swagger UI API документация: http://localhost:8000/docs
   - PgAdmin (для управления базой данных): http://localhost:5050
     - Логин: admin@example.com
     - Пароль: admin

5. Для остановки приложения:
```
docker compose down
```

6. Для остановки и удаления всех данных (включая базу данных):
```
docker compose down -v
```

## Установка и запуск без Docker

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/beauty-salon.git
cd beauty-salon
```

2. Создайте и активируйте виртуальное окружение:
```
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```
pip install -r requirements.txt
```

4. Создайте базу данных PostgreSQL и обновите файл .env с вашими параметрами подключения:
```
DATABASE_URL=postgresql://postgres:password@localhost/beauty_salon
SECRET_KEY=ваш_секретный_ключ
```

5. Запустите приложение:
```
python main.py
```

6. Откройте в браузере http://localhost:8000

## Структура проекта

- `app/` - основной код приложения
  - `api/` - API маршруты
  - `models/` - модели данных
  - `schemas/` - схемы валидации
  - `static/` - статические файлы (CSS, JS)
  - `templates/` - HTML шаблоны
  - `utils/` - вспомогательные функции
- `main.py` - основной файл для запуска приложения
- `requirements.txt` - зависимости проекта
- `Dockerfile` - файл для создания Docker-образа
- `compose.yaml` - файл Docker Compose для оркестрации контейнеров

## Разработка

Для разработки с использованием Docker можно запустить приложение в режиме hot-reload:

```
docker compose -f compose.yaml -f compose.dev.yaml up
```

## API документация

После запуска сервера документация OpenAPI доступна по адресу:
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc 