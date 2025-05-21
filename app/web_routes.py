from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import os
import sys
import json

from app.database import get_db
from app.models import User, Service, Appointment, AppointmentStatus, SalonSettings, Review
from app.utils.auth import verify_password, create_access_token, get_current_user, get_password_hash

# Создаем router для веб-страниц
router = APIRouter(include_in_schema=False)

# Используем глобальный шаблонизатор из main
def get_templates():
    import main
    return main.templates

# Получение настроек салона из базы данных
def get_salon_settings(db: Session):
    from app.admin_routes import get_salon_settings as get_settings
    return get_settings(db)

# Главная страница
@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Получаем популярные услуги для отображения на главной странице
    popular_services = db.query(Service).limit(3).all()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "index.html",
        {
            "request": request, 
            "popular_services": popular_services,
            "settings": salon_settings,
            "user": current_user  # Передаем информацию о пользователе в шаблон
        }
    )

# Страница со списком услуг
@router.get("/services", response_class=HTMLResponse)
async def services_page(
    request: Request,
    category: Optional[str] = None,
    sort: Optional[str] = "name",
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Запрос услуг с фильтрацией и сортировкой
    query = db.query(Service)
    
    # Фильтрация по категории
    if category:
        query = query.filter(Service.category == category)
    
    # Сортировка
    if sort == "price_asc":
        query = query.order_by(Service.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Service.price.desc())
    elif sort == "duration":
        query = query.order_by(Service.duration.asc())
    else:  # По умолчанию по имени
        query = query.order_by(Service.name.asc())
    
    # Пагинация
    limit = 9  # 9 услуг на странице
    offset = (page - 1) * limit
    total = query.count()
    total_pages = (total + limit - 1) // limit
    
    services = query.offset(offset).limit(limit).all()
    
    # Получаем список всех категорий для фильтра
    categories = db.query(Service.category).distinct().all()
    categories = [category[0] for category in categories]
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "services.html",
        {
            "request": request,
            "services": services,
            "categories": categories,
            "selected_category": category,
            "sort": sort,
            "page": page,
            "total_pages": total_pages,
            "settings": salon_settings,
            "user": current_user  # Передаем информацию о пользователе в шаблон
        }
    )

# Страница детальной информации об услуге
@router.get("/services/{service_id}", response_class=HTMLResponse)
async def service_detail(
    request: Request,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Получаем информацию об услуге
    service = db.query(Service).filter(Service.id == service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Получаем похожие услуги той же категории
    similar_services = db.query(Service)\
        .filter(Service.category == service.category, Service.id != service_id)\
        .limit(3)\
        .all()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "service_detail.html",
        {
            "request": request, 
            "service": service, 
            "similar_services": similar_services,
            "settings": salon_settings,
            "user": current_user  # Передаем информацию о пользователе в шаблон
        }
    )

# Страница для записи на услугу
@router.get("/book/{service_id}", response_class=HTMLResponse)
async def booking_page(
    request: Request,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Проверяем авторизацию
    if current_user is None:
        return RedirectResponse(url="/login?next=/book/" + str(service_id), status_code=status.HTTP_302_FOUND)
    
    # Получаем информацию об услуге
    service = db.query(Service).filter(Service.id == service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "booking.html",
        {
            "request": request, 
            "service": service, 
            "user": current_user,
            "settings": salon_settings
        }
    )

# Страница успешной записи
@router.get("/booking-success", response_class=HTMLResponse)
async def booking_success(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "booking_success.html",
        {
            "request": request, 
            "user": current_user,
            "settings": salon_settings
        }
    )

# Страница личного кабинета
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/login?next=/profile", status_code=status.HTTP_302_FOUND)
    
    # Получаем предстоящие записи
    now = datetime.utcnow()
    upcoming_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_time > now,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        )\
        .order_by(Appointment.appointment_time.asc())\
        .all()
    
    # Получаем прошедшие записи
    past_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_time < now,
            Appointment.status == AppointmentStatus.COMPLETED
        )\
        .order_by(Appointment.appointment_time.desc())\
        .all()
    
    # Получаем отмененные записи
    cancelled_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.status == AppointmentStatus.CANCELLED
        )\
        .order_by(Appointment.appointment_time.desc())\
        .all()
    
    # Получаем услуги для каждой записи
    for appointment in upcoming_appointments + past_appointments + cancelled_appointments:
        appointment.service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "upcoming_appointments": upcoming_appointments,
            "past_appointments": past_appointments,
            "cancelled_appointments": cancelled_appointments,
            "settings": salon_settings
        }
    )

# Страница авторизации
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db), next: Optional[str] = None):
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "login.html",
        {
            "request": request, 
            "next": next,
            "settings": salon_settings
        }
    )

@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        print(f"*** Login attempt for: {email} ***")
        # Находим пользователя
        user = db.query(User).filter(User.email == email).first()
        
        # Получаем настройки салона
        salon_settings = get_salon_settings(db)
        
        # Проверяем пользователя и пароль
        if not user:
            print(f"Login failed: User with email {email} not found")
            return get_templates().TemplateResponse(
                "login.html",
                {
                    "request": request, 
                    "error": "Пользователь с таким email не найден", 
                    "email": email,
                    "next": next,
                    "settings": salon_settings
                },
                status_code=401
            )
        
        if not verify_password(password, user.password):
            print(f"Login failed: Invalid password for {email}")
            return get_templates().TemplateResponse(
                "login.html",
                {
                    "request": request, 
                    "error": "Неверный пароль", 
                    "email": email,
                    "next": next,
                    "settings": salon_settings
                },
                status_code=401
            )
        
        # Вход успешный, создаем простой токен (не JWT)
        token_value = f"user_{user.id}_{int(datetime.utcnow().timestamp())}"
        print(f"Login successful for {email}")
        print(f"Generated token: {token_value}")
        
        # Определяем URL для перенаправления
        redirect_url = next or "/"
        
        # Создаем ответ с правильным кодом для POST -> GET редиректа
        response = RedirectResponse(url=redirect_url, status_code=303)  # 303 See Other - правильный код для POST->GET редиректа
        
        # Устанавливаем cookie
        print(f"Setting cookie 'access_token' with value: {token_value}")
        response.set_cookie(
            key="access_token",
            value=token_value,  # Больше не используем Bearer 
            httponly=True,
            max_age=3600,  # 1 час
            path="/"       # Важно! Устанавливаем cookie для всего сайта
        )
        
        print(f"Login successful, redirecting to {redirect_url}")
        return response
    
    except Exception as e:
        print(f"*** ERROR during login: {str(e)} ***")
        import traceback
        print(traceback.format_exc())
        
        return get_templates().TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Произошла ошибка при входе. Пожалуйста, повторите попытку позже.",
                "email": email,
                "next": next,
                "settings": get_salon_settings(db)
            },
            status_code=500
        )

# Страница регистрации
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db), next: Optional[str] = None):
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "register.html",
        {
            "request": request, 
            "next": next,
            "settings": salon_settings
        }
    )

@router.post("/register")
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    agree: bool = Form(...),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    # Проверяем согласие с правилами
    if not agree:
        return get_templates().TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Вы должны принять правила сайта",
                "name": name,
                "email": email,
                "phone": phone,
                "next": next,
                "settings": salon_settings
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем длину пароля
    if len(password) < 8:
        return get_templates().TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пароль должен содержать не менее 8 символов",
                "name": name,
                "email": email,
                "phone": phone,
                "next": next,
                "settings": salon_settings
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем совпадение паролей
    if password != confirm_password:
        return get_templates().TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пароли не совпадают",
                "name": name,
                "email": email,
                "phone": phone,
                "next": next,
                "settings": salon_settings
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем, что пользователь с таким email не существует
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return get_templates().TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пользователь с таким email уже существует",
                "name": name,
                "phone": phone,
                "next": next,
                "settings": salon_settings
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Создаем нового пользователя
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Создаем простой токен (не JWT)
        token_value = f"user_{new_user.id}_{int(datetime.utcnow().timestamp())}"
        print(f"Registration successful for {email}")
        print(f"Generated token: {token_value}")
        
        # Устанавливаем cookie с токеном
        response = RedirectResponse(url=next or "/", status_code=303)  # 303 See Other - правильный код для POST->GET редиректа
        response.set_cookie(
            key="access_token",
            value=token_value,  # Используем тот же формат токена, что и при входе
            httponly=True,
            max_age=3600,  # 1 час
            path="/"        # Важно! Устанавливаем cookie для всего сайта
        )
        
        return response
    except Exception as e:
        # В случае ошибки, возвращаем сообщение об ошибке
        return get_templates().TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": f"Ошибка при регистрации: {str(e)}",
                "name": name,
                "email": email,
                "phone": phone,
                "next": next,
                "settings": salon_settings
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Выход из системы
@router.get("/logout")
async def logout():
    print("Выполнение выхода из системы, удаление cookie access_token")
    response = RedirectResponse(url="/", status_code=303)  # Используем 303 для перенаправления с GET
    
    # Удаляем cookie с разными параметрами для большей надежности
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token")  # На случай, если была установлена без path
    
    print("Cookie access_token удалена, перенаправление на главную страницу")
    return response

# Страница о нас
@router.get("/about", response_class=HTMLResponse)
async def about_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "about.html",
        {
            "request": request,
            "settings": salon_settings,
            "user": current_user  # Передаем информацию о пользователе в шаблон
        }
    )

# Страница контактов
@router.get("/contact", response_class=HTMLResponse)
async def contact_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "contact.html",
        {
            "request": request,
            "settings": salon_settings,
            "user": current_user  # Передаем информацию о пользователе в шаблон
        }
    )

# Маршрут для проверки аутентификации на пути /auth-test
@router.get("/auth-test", response_class=HTMLResponse)
async def auth_test(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Простой маршрут для проверки аутентификации.
    Показывает все доступные cookie и статус аутентификации.
    """
    response = {
        "authenticated": current_user is not None,
        "cookies": {k: v for k, v in request.cookies.items()}
    }
    
    if current_user:
        response["user"] = {
            "id": current_user.id,
            "email": current_user.email,
            "is_admin": current_user.is_admin if hasattr(current_user, 'is_admin') else False,
            "name": current_user.name
        }
    
    user_data = "Не аутентифицирован (гость)"
    if current_user:
        user_data = f"Аутентифицирован как: {current_user.email} (ID: {current_user.id}, Имя: {current_user.name})"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Проверка аутентификации</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .auth-box {{ 
                padding: 20px; 
                border: 1px solid #ccc; 
                border-radius: 8px;
                background-color: #f9f9f9;
                max-width: 600px;
                margin: 0 auto;
            }}
            .auth-status {{ 
                font-weight: bold; 
                color: {("green" if current_user else "red")}; 
            }}
            .cookies {{
                margin-top: 20px;
                font-family: monospace;
                background-color: #eee;
                padding: 10px;
                border-radius: 4px;
                word-break: break-all;
            }}
            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow: auto; }}
        </style>
    </head>
    <body>
        <div class="auth-box">
            <h2>Статус аутентификации</h2>
            <p class="auth-status">{user_data}</p>
            
            <div class="cookies">
                <h3>Cookies:</h3>
                <pre>{dict(request.cookies)}</pre>
            </div>
            
            <h3>Данные запроса:</h3>
            <pre>{json.dumps(response, indent=2, ensure_ascii=False)}</pre>
            
            <div style="margin-top: 30px;">
                <a href="/">На главную</a> | 
                <a href="/login">Войти</a> | 
                <a href="/logout">Выйти</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

# Дополнительный маршрут по пути /test-auth (для обеспечения совместимости)
@router.get("/test-auth")
async def test_auth(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """
    Переадресация на /auth-test для обеспечения совместимости.
    """
    return RedirectResponse(url="/auth-test", status_code=303)

# Страница с записями пользователя
@router.get("/appointments", response_class=HTMLResponse)
async def appointments_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/login?next=/appointments", status_code=status.HTTP_302_FOUND)
    
    # Получаем предстоящие записи
    now = datetime.utcnow()
    upcoming_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_time > now,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        )\
        .order_by(Appointment.appointment_time.asc())\
        .all()
    
    # Получаем прошедшие записи
    past_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_time < now,
            Appointment.status == AppointmentStatus.COMPLETED
        )\
        .order_by(Appointment.appointment_time.desc())\
        .all()
    
    # Получаем отмененные записи
    cancelled_appointments = db.query(Appointment)\
        .filter(
            Appointment.user_id == current_user.id,
            Appointment.status == AppointmentStatus.CANCELLED
        )\
        .order_by(Appointment.appointment_time.desc())\
        .all()
    
    # Получаем услуги для каждой записи
    for appointment in upcoming_appointments + past_appointments + cancelled_appointments:
        appointment.service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "appointments.html",
        {
            "request": request,
            "user": current_user,
            "upcoming_appointments": upcoming_appointments,
            "past_appointments": past_appointments,
            "cancelled_appointments": cancelled_appointments,
            "settings": salon_settings
        }
    )

# Страница отзывов
@router.get("/reviews", response_class=HTMLResponse)
async def reviews_page(
    request: Request,
    service_id: Optional[int] = None,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Страница со списком отзывов.
    """
    # Размер страницы
    page_size = 10
    offset = (page - 1) * page_size
    
    # Получаем только одобренные отзывы
    query = db.query(Review).filter(Review.status == Review.ReviewStatus.APPROVED)
    
    # Фильтрация по услуге
    if service_id:
        query = query.filter(Review.service_id == service_id)
        selected_service = db.query(Service).filter(Service.id == service_id).first()
    else:
        selected_service = None
    
    # Сортировка и подсчет
    query = query.order_by(Review.created_at.desc())
    total = query.count()
    
    # Пагинация
    reviews = query.offset(offset).limit(page_size).all()
    
    # Загружаем информацию о пользователях и услугах
    for review in reviews:
        review.user = db.query(User).filter(User.id == review.user_id).first()
        if review.service_id:
            review.service = db.query(Service).filter(Service.id == review.service_id).first()
    
    # Всего страниц
    total_pages = (total + page_size - 1) // page_size
    
    # Получаем список услуг для фильтра
    services = db.query(Service).order_by(Service.name).all()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "reviews.html",
        {
            "request": request,
            "user": current_user,
            "reviews": reviews,
            "services": services,
            "selected_service": selected_service,
            "page": page,
            "total_pages": total_pages,
            "total_reviews": total,
            "settings": salon_settings
        }
    )

# Страница добавления отзыва
@router.get("/reviews/add", response_class=HTMLResponse)
async def add_review_page(
    request: Request,
    service_id: Optional[int] = None,
    appointment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Страница добавления нового отзыва.
    """
    # Проверяем авторизацию
    if current_user is None:
        return RedirectResponse(url="/login?next=/reviews/add", status_code=status.HTTP_302_FOUND)
    
    # Проверяем параметры
    service = None
    appointment = None
    
    if service_id:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    if appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.user_id == current_user.id
        ).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Запись не найдена или не принадлежит вам")
        
        # Проверяем, был ли уже оставлен отзыв для этой записи
        existing_review = db.query(Review).filter(
            Review.appointment_id == appointment_id
        ).first()
        
        if existing_review:
            return RedirectResponse(url=f"/reviews?message=already_reviewed", status_code=status.HTTP_302_FOUND)
        
        # Если запись указана, то автоматически заполняем услугу
        if appointment.service_id and not service:
            service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Если не указана ни услуга, ни запись, показываем список услуг
    if not service and not appointment:
        services = db.query(Service).order_by(Service.name).all()
    else:
        services = None
    
    # Получаем завершенные записи пользователя для выбора
    completed_appointments = []
    if not appointment:
        completed_appointments = db.query(Appointment).filter(
            Appointment.user_id == current_user.id,
            Appointment.status == AppointmentStatus.COMPLETED
        ).order_by(Appointment.appointment_time.desc()).all()
        
        # Исключаем записи, для которых уже есть отзывы
        appointments_with_reviews = db.query(Review.appointment_id).filter(
            Review.appointment_id.in_([a.id for a in completed_appointments])
        ).all()
        
        appointments_with_reviews_ids = [a[0] for a in appointments_with_reviews]
        completed_appointments = [a for a in completed_appointments if a.id not in appointments_with_reviews_ids]
        
        # Загружаем информацию об услугах
        for a in completed_appointments:
            a.service = db.query(Service).filter(Service.id == a.service_id).first()
    
    # Получаем настройки салона
    salon_settings = get_salon_settings(db)
    
    return get_templates().TemplateResponse(
        "add_review.html",
        {
            "request": request,
            "user": current_user,
            "service": service,
            "appointment": appointment,
            "services": services,
            "completed_appointments": completed_appointments,
            "settings": salon_settings
        }
    ) 