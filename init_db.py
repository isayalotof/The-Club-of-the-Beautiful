import os
import time
from sqlalchemy import create_engine
from app.database import Base
from app.models import User, Service, Appointment, SalonSettings
from app.utils.auth import get_password_hash
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем строку подключения
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    # Ожидаем запуска базы данных
    for i in range(5):
        try:
            engine = create_engine(DATABASE_URL)
            connection = engine.connect()
            connection.close()
            print("Успешное подключение к базе данных")
            break
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            print(f"Повторная попытка через 5 секунд...")
            time.sleep(5)
    else:
        print("Не удалось подключиться к базе данных")
        return

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы")

    # Создаем админ-пользователя, если он не существует
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    admin_email = "admin@example.com"
    if not session.query(User).filter(User.email == admin_email).first():
        admin_user = User(
            email=admin_email,
            name="Администратор",
            phone="+7 (999) 123-45-67",
            password=get_password_hash("adminpassword"),
            is_admin=True
        )
        session.add(admin_user)
        session.commit()
        print(f"Создан администратор с email {admin_email} и паролем 'adminpassword'")

    # Создаем образцы услуг, если их нет
    if session.query(Service).count() == 0:
        services = [
            Service(
                name="Классический массаж лица",
                description="Массаж лица с использованием классической техники для улучшения кровообращения и тонуса кожи.",
                price=2500.0,
                duration=60,
                category="Уход за лицом",
                image_url="/static/images/facial-massage.jpg"
            ),
            Service(
                name="Общий массаж тела",
                description="Расслабляющий массаж всего тела для снятия напряжения и улучшения самочувствия.",
                price=4000.0,
                duration=90,
                category="Массаж",
                image_url="/static/images/body-massage.jpg"
            ),
            Service(
                name="Чистка лица",
                description="Глубокая чистка лица с использованием профессиональной косметики для удаления загрязнений и омертвевших клеток.",
                price=3000.0,
                duration=75,
                category="Уход за лицом",
                image_url="/static/images/facial-cleaning.jpg"
            ),
            Service(
                name="Антицеллюлитный массаж",
                description="Интенсивный массаж для борьбы с целлюлитом и улучшения внешнего вида кожи.",
                price=3500.0,
                duration=60,
                category="Массаж",
                image_url="/static/images/anti-cellulite.jpg"
            ),
            Service(
                name="Маникюр с покрытием гель-лаком",
                description="Классический маникюр с нанесением стойкого гель-лака.",
                price=1800.0,
                duration=90,
                category="Ногтевой сервис",
                image_url="/static/images/manicure.jpg"
            ),
        ]
        
        session.add_all(services)
        session.commit()
        print(f"Добавлено {len(services)} образцов услуг")
        
    # Создаем настройки салона, если они не существуют
    if session.query(SalonSettings).filter(SalonSettings.key == "general").first() is None:
        general_settings = SalonSettings(
            key="general",
            value={
                "salon_name": "Салон красоты",
                "salon_description": "Наш салон красоты предлагает широкий спектр услуг для вашего комфорта и красоты. Профессиональные мастера и высококачественная косметика.",
                "salon_address": "г. Москва, ул. Примерная, д. 123",
                "salon_phone": "+7 (999) 123-45-67",
                "salon_email": "info@salon.ru"
            }
        )
        session.add(general_settings)
        print("Добавлены общие настройки салона")
        
    if session.query(SalonSettings).filter(SalonSettings.key == "schedule").first() is None:
        schedule_settings = SalonSettings(
            key="schedule",
            value={
                "monday": "9:00 - 20:00",
                "tuesday": "9:00 - 20:00",
                "wednesday": "9:00 - 20:00",
                "thursday": "9:00 - 20:00",
                "friday": "9:00 - 20:00",
                "saturday": "10:00 - 18:00",
                "sunday": "выходной"
            }
        )
        session.add(schedule_settings)
        print("Добавлено расписание работы салона")
        
    if session.query(SalonSettings).filter(SalonSettings.key == "social").first() is None:
        social_settings = SalonSettings(
            key="social",
            value={
                "facebook": "https://facebook.com/salon",
                "instagram": "https://instagram.com/salon",
                "vk": "https://vk.com/salon",
                "telegram": "https://t.me/salon"
            }
        )
        session.add(social_settings)
        print("Добавлены ссылки на социальные сети")
        
    if session.query(SalonSettings).filter(SalonSettings.key == "seo").first() is None:
        seo_settings = SalonSettings(
            key="seo",
            value={
                "meta_title": "Салон красоты - профессиональные услуги красоты",
                "meta_description": "Салон красоты предлагает широкий спектр услуг: массаж, уход за лицом, маникюр, педикюр и многое другое.",
                "meta_keywords": "салон красоты, массаж, уход за лицом, СПА, маникюр, педикюр"
            }
        )
        session.add(seo_settings)
        print("Добавлены настройки SEO")
        
    session.commit()
    session.close()
    print("Инициализация базы данных завершена")

if __name__ == "__main__":
    init_db() 