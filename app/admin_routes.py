from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
import json
import os
import shutil
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Service, Appointment, AppointmentStatus, SalonSettings
from app.schemas import SalonSettingsSchema, GeneralSettings, ScheduleSettings, SocialSettings, SeoSettings
from app.utils.auth import get_current_user, get_current_active_admin
from app.models.reviews import Review, ReviewStatus

# Создаем router для админ-панели
router = APIRouter(prefix="/admin", include_in_schema=False)

# Используем глобальный шаблонизатор из main
def get_templates():
    import main
    return main.templates

# Получение настроек салона из базы данных
def get_salon_settings(db: Session) -> SalonSettingsSchema:
    settings = SalonSettingsSchema()
    
    # Загружаем настройки из базы данных
    for key in ["general", "schedule", "social", "seo"]:
        db_setting = db.query(SalonSettings).filter(SalonSettings.key == key).first()
        if db_setting:
            setattr(settings, key, type(getattr(settings, key))(**db_setting.value))
    
    # Загружаем URL логотипа
    logo_setting = db.query(SalonSettings).filter(SalonSettings.key == "logo_url").first()
    if logo_setting and logo_setting.value.get("url"):
        settings.logo_url = logo_setting.value.get("url")
    
    return settings

# Сохранение настроек салона в базу данных
def save_salon_setting(db: Session, key: str, value: Dict[str, Any]) -> None:
    db_setting = db.query(SalonSettings).filter(SalonSettings.key == key).first()
    
    if db_setting:
        db_setting.value = value
    else:
        db_setting = SalonSettings(key=key, value=value)
        db.add(db_setting)
    
    db.commit()
    db.refresh(db_setting)

# Главная страница админ-панели (дашборд)
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Статистика салона
    services_count = db.query(func.count(Service.id)).scalar()
    
    now = datetime.utcnow()
    active_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_time > now,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    ).scalar()
    
    users_count = db.query(func.count(User.id)).scalar()
    
    stats = {
        "services_count": services_count,
        "appointments_count": active_appointments,
        "users_count": users_count
    }
    
    # Получаем последние записи
    recent_appointments = db.query(Appointment).order_by(
        Appointment.created_at.desc()
    ).limit(5).all()
    
    for appointment in recent_appointments:
        appointment.user = db.query(User).filter(User.id == appointment.user_id).first()
        appointment.service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Получаем популярные услуги
    # Подсчитываем количество записей для каждой услуги
    popular_services_query = db.query(
        Service,
        func.count(Appointment.id).label("bookings_count")
    ).join(
        Appointment, Service.id == Appointment.service_id
    ).group_by(
        Service.id
    ).order_by(
        func.count(Appointment.id).desc()
    ).limit(5)
    
    popular_services = []
    for service, bookings_count in popular_services_query:
        service.bookings_count = bookings_count
        popular_services.append(service)
    
    return get_templates().TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "active": "dashboard",
            "stats": stats,
            "recent_appointments": recent_appointments,
            "popular_services": popular_services
        }
    )

# Управление услугами
@router.get("/services", response_class=HTMLResponse)
async def admin_services(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    services = db.query(Service).all()
    
    # Получаем уникальные категории для выпадающего списка
    categories = db.query(Service.category).distinct().all()
    categories = [category[0] for category in categories]
    
    return get_templates().TemplateResponse(
        "admin/services.html",
        {
            "request": request,
            "user": current_user,
            "active": "services",
            "services": services,
            "categories": categories
        }
    )

# Добавление новой услуги
@router.post("/services", response_class=RedirectResponse)
async def add_service(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    category: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем новую услугу
    new_service = Service(
        name=name,
        description=description,
        price=price,
        duration=duration,
        category=category
    )
    
    # Если загружено изображение, сохраняем его
    if image and image.filename:
        # Создаем директорию для изображений, если она не существует
        UPLOAD_DIR = "app/static/uploads/services"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = image.filename.split(".")[-1]
        file_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{name.replace(' ', '_')}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Сохраняем URL в базе данных
        new_service.image_url = f"/static/uploads/services/{file_name}"
    
    db.add(new_service)
    db.commit()
    
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_303_SEE_OTHER)

# Управление записями
@router.get("/appointments", response_class=HTMLResponse)
async def admin_appointments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[int] = None
):
    # Базовый запрос для получения записей
    query = db.query(Appointment)
    
    # Применяем фильтры, если они заданы
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Appointment.appointment_time >= date_from_obj)
        except ValueError:
            pass  # Игнорируем некорректный формат даты
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            # Добавляем 1 день, чтобы включить все записи за указанную дату
            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.filter(Appointment.appointment_time < date_to_obj)
        except ValueError:
            pass  # Игнорируем некорректный формат даты

    # Фильтр по пользователю
    if user_id:
        query = query.filter(Appointment.user_id == user_id)
        # Получаем данные пользователя для отображения
        selected_user = db.query(User).filter(User.id == user_id).first()
    else:
        selected_user = None
    
    # Сортируем по дате (сначала новые)
    query = query.order_by(Appointment.appointment_time.desc())
    
    # Выполняем запрос
    appointments = query.all()
    
    # Загружаем связанные данные (пользователи и услуги)
    for appointment in appointments:
        appointment.user = db.query(User).filter(User.id == appointment.user_id).first()
        appointment.service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Получаем доступные статусы для фильтра
    statuses = [status.value for status in AppointmentStatus]
    
    return get_templates().TemplateResponse(
        "admin/appointments.html",
        {
            "request": request,
            "user": current_user,
            "active": "appointments",
            "appointments": appointments,
            "statuses": statuses,
            "current_status": status_filter,
            "date_from": date_from,
            "date_to": date_to,
            "selected_user": selected_user,
            "user_id": user_id
        }
    )

# Обновление статуса записи
@router.post("/appointments/{appointment_id}/update-status", response_class=RedirectResponse)
async def update_appointment_status(
    request: Request,
    appointment_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Находим запись по ID
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверяем, что статус валиден
    if status not in [s.value for s in AppointmentStatus]:
        raise HTTPException(status_code=400, detail="Некорректный статус")
    
    # Обновляем статус
    appointment.status = status
    db.commit()
    
    return RedirectResponse(url="/admin/appointments", status_code=status.HTTP_303_SEE_OTHER)

# Управление пользователями
@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Базовый запрос
    query = db.query(User)
    
    # Применяем фильтры
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )
    
    if role:
        if role == "admin":
            query = query.filter(User.is_admin == True)
        elif role == "user":
            query = query.filter(User.is_admin == False)
    
    # Сортируем по id
    query = query.order_by(User.id.asc())
    
    # Получаем пользователей
    users = query.all()
    
    return get_templates().TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": current_user,
            "active": "users",
            "users": users,
            "search": search,
            "role": role
        }
    )

# Изменение роли пользователя
@router.post("/users/{user_id}/toggle-admin", response_class=RedirectResponse)
async def toggle_admin_role(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем пользователя по ID
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя лишить админских прав себя
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Вы не можете изменить свою роль")
    
    # Меняем роль
    user.is_admin = not user.is_admin
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)

# Редактирование услуги
@router.post("/services/edit", response_class=RedirectResponse)
async def edit_service(
    request: Request,
    id: int = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    category: str = Form(...),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Находим услугу по ID
    service = db.query(Service).filter(Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Обновляем данные
    service.name = name
    service.description = description
    service.price = price
    service.duration = duration
    service.category = category
    
    # Удаляем изображение, если запрошено
    if remove_image and service.image_url:
        # Удаляем файл, если он существует
        file_path = f"app/{service.image_url[1:]}"  # Убираем первый слеш
        if os.path.exists(file_path):
            os.remove(file_path)
        service.image_url = None
    
    # Если загружено новое изображение, заменяем старое
    if image and image.filename:
        # Удаляем старое изображение, если оно существует
        if service.image_url:
            old_file_path = f"app/{service.image_url[1:]}"  # Убираем первый слеш
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Создаем директорию для изображений, если она не существует
        UPLOAD_DIR = "app/static/uploads/services"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = image.filename.split(".")[-1]
        file_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{name.replace(' ', '_')}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Сохраняем URL в базе данных
        service.image_url = f"/static/uploads/services/{file_name}"
    
    db.commit()
    
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_303_SEE_OTHER)

# Удаление услуги
@router.post("/services/delete", response_class=RedirectResponse)
async def delete_service(
    request: Request,
    id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Находим услугу по ID
    service = db.query(Service).filter(Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Удаляем изображение, если оно существует
    if service.image_url:
        file_path = f"app/{service.image_url[1:]}"  # Убираем первый слеш
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Удаляем связанные записи на услугу
    db.query(Appointment).filter(Appointment.service_id == id).delete()
    
    # Удаляем услугу
    db.delete(service)
    db.commit()
    
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_303_SEE_OTHER)

# Страница настроек
@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Получаем настройки салона
    settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "user": current_user,
            "active": "settings",
            "settings": settings
        }
    )

# Сохранение общих настроек
@router.post("/settings/general", response_class=RedirectResponse)
async def save_general_settings(
    request: Request,
    salon_name: str = Form(...),
    salon_description: Optional[str] = Form(None),
    salon_address: Optional[str] = Form(None),
    salon_phone: Optional[str] = Form(None),
    salon_email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем объект с настройками
    general_settings = {
        "salon_name": salon_name,
        "salon_description": salon_description,
        "salon_address": salon_address,
        "salon_phone": salon_phone,
        "salon_email": salon_email
    }
    
    # Сохраняем настройки в базу данных
    save_salon_setting(db, "general", general_settings)
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)

# Сохранение расписания работы
@router.post("/settings/schedule", response_class=RedirectResponse)
async def save_schedule_settings(
    request: Request,
    monday: Optional[str] = Form(None),
    tuesday: Optional[str] = Form(None),
    wednesday: Optional[str] = Form(None),
    thursday: Optional[str] = Form(None),
    friday: Optional[str] = Form(None),
    saturday: Optional[str] = Form(None),
    sunday: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем объект с настройками
    schedule_settings = {
        "monday": monday or "9:00 - 20:00",
        "tuesday": tuesday or "9:00 - 20:00",
        "wednesday": wednesday or "9:00 - 20:00",
        "thursday": thursday or "9:00 - 20:00",
        "friday": friday or "9:00 - 20:00",
        "saturday": saturday or "10:00 - 18:00",
        "sunday": sunday or "выходной"
    }
    
    # Сохраняем настройки в базу данных
    save_salon_setting(db, "schedule", schedule_settings)
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)

# Сохранение ссылок на социальные сети
@router.post("/settings/social", response_class=RedirectResponse)
async def save_social_settings(
    request: Request,
    facebook: Optional[str] = Form(None),
    instagram: Optional[str] = Form(None),
    vk: Optional[str] = Form(None),
    telegram: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем объект с настройками
    social_settings = {
        "facebook": facebook,
        "instagram": instagram,
        "vk": vk,
        "telegram": telegram
    }
    
    # Сохраняем настройки в базу данных
    save_salon_setting(db, "social", social_settings)
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)

# Сохранение настроек SEO
@router.post("/settings/seo", response_class=RedirectResponse)
async def save_seo_settings(
    request: Request,
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем объект с настройками
    seo_settings = {
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords
    }
    
    # Сохраняем настройки в базу данных
    save_salon_setting(db, "seo", seo_settings)
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)

# Загрузка логотипа
@router.post("/settings/logo", response_class=RedirectResponse)
async def upload_logo(
    request: Request,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Создаем директорию для логотипа, если она не существует
    UPLOAD_DIR = "app/static/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Генерируем имя файла
    file_extension = logo.filename.split(".")[-1]
    file_name = f"logo.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    # Удаляем старый логотип, если он существует
    logo_setting = db.query(SalonSettings).filter(SalonSettings.key == "logo_url").first()
    if logo_setting and logo_setting.value.get("url"):
        old_file_path = f"app/{logo_setting.value['url'][1:]}"  # Убираем первый слеш
        if os.path.exists(old_file_path):
            os.remove(old_file_path)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(logo.file, buffer)
    
    # Сохраняем URL в базу данных
    logo_url = f"/static/uploads/{file_name}"
    save_salon_setting(db, "logo_url", {"url": logo_url})
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/reviews")
async def admin_reviews(
    request: Request,
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    service_id: Optional[int] = None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Маршрут для управления отзывами в админ-панели."""
    # Проверка прав администратора
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Количество отзывов на странице
    page_size = 10
    offset = (page - 1) * page_size
    
    # Формирование запроса с фильтрами
    query = db.query(Review).outerjoin(Service)
    
    # Применение фильтров
    if status:
        try:
            review_status = ReviewStatus(status)
            query = query.filter(Review.status == review_status)
        except ValueError:
            # Неверный статус, игнорируем фильтр
            pass
    
    if service_id:
        query = query.filter(Review.service_id == service_id)
    
    # Получение общего количества отзывов для пагинации
    total_reviews = query.count()
    
    # Сортировка по дате создания (сначала новые)
    query = query.order_by(Review.created_at.desc())
    
    # Применение пагинации
    reviews = query.offset(offset).limit(page_size).all()
    
    # Загрузка связанных данных для шаблона
    for review in reviews:
        db.refresh(review)
    
    # Получение всех услуг для фильтра
    services = db.query(Service).all()
    
    # Расчет параметров пагинации
    total_pages = (total_reviews + page_size - 1) // page_size
    
    # Формирование статистики по статусам
    status_counts = {
        "all": db.query(Review).count(),
        "pending": db.query(Review).filter(Review.status == ReviewStatus.PENDING).count(),
        "approved": db.query(Review).filter(Review.status == ReviewStatus.APPROVED).count(),
        "rejected": db.query(Review).filter(Review.status == ReviewStatus.REJECTED).count()
    }
    
    return get_templates().TemplateResponse(
        "admin/reviews.html",
        {
            "request": request,
            "user": current_user,
            "reviews": reviews,
            "services": services,
            "total_reviews": total_reviews,
            "page": page,
            "total_pages": total_pages,
            "page_size": page_size,
            "current_status": status,
            "current_service_id": service_id,
            "status_counts": status_counts,
            "ReviewStatus": ReviewStatus,
            "active": "reviews"
        }
    ) 