#!/bin/sh
set -e

# Устанавливаем все зависимости
pip install --no-cache-dir -r requirements.txt

# Создаем необходимые директории для статических файлов
mkdir -p app/static/uploads/services
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/images

# Запускаем инициализацию базы данных
python init_db.py
 
# Запускаем основное приложение
exec uvicorn main:app --host 0.0.0.0 --port 8000 