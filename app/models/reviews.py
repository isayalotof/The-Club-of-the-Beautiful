import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ReviewStatus(str, enum.Enum):
    """Статусы отзыва"""
    PENDING = "pending"    # Ожидает проверки
    APPROVED = "approved"  # Одобрен
    REJECTED = "rejected"  # Отклонен

class Review(Base):
    """Модель отзыва клиента"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с пользователем (опционально, если у нас есть модель юзера)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="reviews")
    
    # Связь с услугой (опционально)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service = relationship("Service", back_populates="reviews")
    
    # Связь с записью (опционально)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    appointment = relationship("Appointment", back_populates="review")
    
    # Данные отзыва
    rating = Column(Float, nullable=False)  # Оценка от 1 до 5
    text = Column(Text, nullable=False)  # Текст отзыва
    
    # Служебные поля
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    admin_comment = Column(Text, nullable=True)  # Комментарий администратора
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Имя и email клиента (если отзыв от не зарегистрированного клиента)
    client_name = Column(String(100), nullable=True)
    client_email = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<Review(id={self.id}, rating={self.rating}, status={self.status})>" 