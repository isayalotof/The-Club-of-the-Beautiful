from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.reviews import ReviewStatus

# Схема базового отзыва
class ReviewBase(BaseModel):
    service_id: Optional[int] = None
    appointment_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)  # Оценка от 1 до 5
    text: str = Field(..., min_length=10, max_length=1000)  # Текст отзыва

# Схема для создания отзыва
class ReviewCreate(ReviewBase):
    pass

# Схема для обновления отзыва
class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = Field(None, min_length=10, max_length=1000)
    status: Optional[ReviewStatus] = None
    admin_comment: Optional[str] = None

# Полная схема отзыва для ответа
class Review(ReviewBase):
    id: int
    user_id: int
    status: ReviewStatus
    admin_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# Схема для списка отзывов
class ReviewList(BaseModel):
    reviews: List[Review]
    total: int 