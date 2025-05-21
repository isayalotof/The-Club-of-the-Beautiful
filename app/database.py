import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time

# Загружаем переменные среды из .env файла
load_dotenv()

# Получаем строку подключения из переменных среды
DATABASE_URL = os.getenv("DATABASE_URL")

# Функция для подключения к БД с повторными попытками
def connect_with_retry(database_url, max_retries=5, retry_interval=5):
    retries = 0
    while retries < max_retries:
        try:
            engine = create_engine(database_url)
            # Проверяем соединение
            connection = engine.connect()
            connection.close()
            print("Успешное соединение с базой данных!")
            return engine
        except Exception as e:
            retries += 1
            print(f"Ошибка соединения с базой данных: {e}")
            print(f"Повторная попытка {retries}/{max_retries} через {retry_interval} секунд...")
            time.sleep(retry_interval)
    
    # Если все попытки исчерпаны
    raise Exception("Не удалось подключиться к базе данных после нескольких попыток")

# Создаем движок SQLAlchemy с повторными попытками
engine = connect_with_retry(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 