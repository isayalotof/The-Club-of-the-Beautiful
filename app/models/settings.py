from sqlalchemy import Column, Integer, String, Text, JSON
from app.database import Base

class SalonSettings(Base):
    __tablename__ = "salon_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(JSON)
    
    # Типичные ключи настроек:
    # general - общая информация о салоне (название, описание, адрес, телефон, email)
    # schedule - расписание работы
    # social - ссылки на социальные сети
    # seo - настройки SEO
    # logo_url - путь к логотипу салона 