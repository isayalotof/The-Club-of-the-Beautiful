from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    duration = Column(Integer)  # Продолжительность в минутах
    category = Column(String, index=True)  # Категория услуги (массаж, уход за лицом, и т.д.)
    image_url = Column(String, nullable=True)  # Ссылка на изображение
    
    # Отношение к записям на услуги
    appointments = relationship("Appointment", back_populates="service")
    
    # Отношение к отзывам
    reviews = relationship("Review", back_populates="service") 