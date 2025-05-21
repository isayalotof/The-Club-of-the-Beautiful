FROM python:3.11-slim

WORKDIR /app

# Добавляем зависимости для psycopg2 и инструменты отладки
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Установка всех зависимостей
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir email-validator

COPY . .

# Делаем entrypoint скрипт исполняемым
RUN chmod +x docker-entrypoint.sh

# Переменные среды по умолчанию
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/beauty_salon
ENV SECRET_KEY=your_secret_key_here
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"] 