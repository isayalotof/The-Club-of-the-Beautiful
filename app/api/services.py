from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Service, User
from app.schemas import ServiceCreate, Service as ServiceSchema, ServiceUpdate, ServiceList
from app.utils.auth import get_current_active_admin

router = APIRouter()

@router.get("", response_model=ServiceList)
def get_services(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Запрос для получения услуг
    query = db.query(Service)
    
    # Фильтрация по категории, если указана
    if category:
        query = query.filter(Service.category == category)
    
    # Общее количество услуг после фильтрации
    total = query.count()
    
    # Пагинация
    services = query.offset(skip).limit(limit).all()
    
    return {"services": services, "total": total}

@router.get("/{service_id}", response_model=ServiceSchema)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service

@router.post("", response_model=ServiceSchema)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем новую услугу
    db_service = Service(
        name=service.name,
        description=service.description,
        price=service.price,
        duration=service.duration,
        category=service.category,
        image_url=service.image_url
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.put("/{service_id}", response_model=ServiceSchema)
def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем существующую услугу
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Обновляем поля услуги
    if service_update.name is not None:
        db_service.name = service_update.name
    if service_update.description is not None:
        db_service.description = service_update.description
    if service_update.price is not None:
        db_service.price = service_update.price
    if service_update.duration is not None:
        db_service.duration = service_update.duration
    if service_update.category is not None:
        db_service.category = service_update.category
    if service_update.image_url is not None:
        db_service.image_url = service_update.image_url
    
    db.commit()
    db.refresh(db_service)
    return db_service

@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем существующую услугу
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Удаляем услугу
    db.delete(db_service)
    db.commit()
    return {"message": "Услуга успешно удалена"} 