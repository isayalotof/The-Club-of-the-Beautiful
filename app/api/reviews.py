from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.reviews import Review, ReviewStatus
from app.models import User, Service
from app.schemas import ReviewCreate, Review as ReviewSchema, ReviewUpdate, ReviewList
from app.utils.auth import get_current_user, get_current_active_admin

router = APIRouter()

@router.get("", response_model=ReviewList)
def get_reviews(
    skip: int = 0,
    limit: int = 10,
    status: Optional[ReviewStatus] = None,
    service_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Запрос для получения отзывов
    query = db.query(Review)
    
    # Фильтрация по статусу, если указан
    if status:
        query = query.filter(Review.status == status)
    
    # Фильтрация по услуге, если указана
    if service_id:
        query = query.filter(Review.service_id == service_id)
    
    # Общее количество отзывов после фильтрации
    total = query.count()
    
    # Пагинация
    reviews = query.offset(skip).limit(limit).all()
    
    return {"reviews": reviews, "total": total}

@router.get("/public", response_model=ReviewList)
def get_public_reviews(
    skip: int = 0,
    limit: int = 10,
    service_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    # Запрос для получения только опубликованных отзывов
    query = db.query(Review).filter(Review.status == ReviewStatus.APPROVED)
    
    # Фильтрация по услуге, если указана
    if service_id:
        query = query.filter(Review.service_id == service_id)
    
    # Общее количество отзывов после фильтрации
    total = query.count()
    
    # Пагинация и сортировка по дате (новые сначала)
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"reviews": reviews, "total": total}

@router.get("/{review_id}", response_model=ReviewSchema)
def get_review(
    review_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if review is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Если пользователь не админ и не автор отзыва, и отзыв не одобрен - запрещаем доступ
    if not current_user.is_admin and review.user_id != current_user.id and review.status != ReviewStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
        
    return review

@router.post("", response_model=ReviewSchema)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Проверяем, существует ли услуга
    service = db.query(Service).filter(Service.id == review.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Создаем новый отзыв
    db_review = Review(
        service_id=review.service_id,
        rating=review.rating,
        text=review.text,
        client_name=review.client_name if not current_user else current_user.full_name,
        client_email=review.client_email if not current_user else current_user.email,
        status=ReviewStatus.PENDING,
        user_id=current_user.id if current_user else None
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.put("/{review_id}/status", response_model=ReviewSchema)
def update_review_status(
    review_id: int,
    status: ReviewStatus,
    admin_comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем существующий отзыв
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Обновляем статус и комментарий администратора
    db_review.status = status
    if admin_comment:
        db_review.admin_comment = admin_comment
    
    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем существующий отзыв
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Удаляем отзыв
    db.delete(db_review)
    db.commit()
    return {"message": "Отзыв успешно удален"} 