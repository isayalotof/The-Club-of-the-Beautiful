from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Appointment, AppointmentStatus, User, Service
from app.schemas import AppointmentCreate, Appointment as AppointmentSchema, AppointmentUpdate, AppointmentDetail, AppointmentList
from app.utils.auth import get_current_user, get_current_active_admin
from app.utils.notifications import notify_new_appointment, notify_appointment_status_change

router = APIRouter()

@router.get("", response_model=AppointmentList)
def get_appointments(
    skip: int = 0,
    limit: int = 10,
    status: Optional[AppointmentStatus] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Базовый запрос
    query = db.query(Appointment)
    
    # Если пользователь не админ, показываем только его записи
    if not current_user.is_admin:
        query = query.filter(Appointment.user_id == current_user.id)
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Appointment.status == status)
    
    # Фильтрация по дате
    if from_date:
        query = query.filter(Appointment.appointment_time >= from_date)
    if to_date:
        query = query.filter(Appointment.appointment_time <= to_date)
    
    # Сортировка по дате
    query = query.order_by(Appointment.appointment_time.desc())
    
    # Общее количество записей после фильтрации
    total = query.count()
    
    # Пагинация
    appointments = query.offset(skip).limit(limit).all()
    
    # Получаем детали для каждой записи
    appointments_with_details = []
    for appointment in appointments:
        user = db.query(User).filter(User.id == appointment.user_id).first()
        service = db.query(Service).filter(Service.id == appointment.service_id).first()
        appointment_dict = {
            **appointment.__dict__,
            "user": user,
            "service": service
        }
        appointments_with_details.append(appointment_dict)
    
    return {"appointments": appointments_with_details, "total": total}

@router.get("/my", response_model=AppointmentList)
def get_my_appointments(
    skip: int = 0,
    limit: int = 10,
    status: Optional[AppointmentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Запрос для получения записей текущего пользователя
    query = db.query(Appointment).filter(Appointment.user_id == current_user.id)
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Appointment.status == status)
    
    # Сортировка по дате
    query = query.order_by(Appointment.appointment_time.desc())
    
    # Общее количество записей после фильтрации
    total = query.count()
    
    # Пагинация
    appointments = query.offset(skip).limit(limit).all()
    
    # Получаем детали для каждой записи
    appointments_with_details = []
    for appointment in appointments:
        user = db.query(User).filter(User.id == appointment.user_id).first()
        service = db.query(Service).filter(Service.id == appointment.service_id).first()
        appointment_dict = {
            **appointment.__dict__,
            "user": user,
            "service": service
        }
        appointments_with_details.append(appointment_dict)
    
    return {"appointments": appointments_with_details, "total": total}

@router.get("/{appointment_id}", response_model=AppointmentDetail)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем запись
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверяем права доступа
    if not current_user.is_admin and appointment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой записи")
    
    # Получаем дополнительную информацию
    user = db.query(User).filter(User.id == appointment.user_id).first()
    service = db.query(Service).filter(Service.id == appointment.service_id).first()
    
    # Создаем объект с деталями
    appointment_detail = {
        **appointment.__dict__,
        "user": user,
        "service": service
    }
    
    return appointment_detail

@router.post("", response_model=AppointmentSchema)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем существование услуги
    service = db.query(Service).filter(Service.id == appointment.service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Проверяем доступность времени
    appointment_end_time = appointment.appointment_time + timedelta(minutes=service.duration)
    overlapping_appointments = db.query(Appointment).filter(
        Appointment.appointment_time < appointment_end_time,
        Appointment.appointment_time + timedelta(minutes=service.duration) > appointment.appointment_time,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    ).all()
    
    if overlapping_appointments:
        raise HTTPException(status_code=400, detail="Выбранное время уже занято")
    
    # Создаем новую запись
    db_appointment = Appointment(
        user_id=current_user.id,
        service_id=appointment.service_id,
        appointment_time=appointment.appointment_time,
        notes=appointment.notes,
        status=AppointmentStatus.PENDING
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # Отправляем уведомление о новой записи
    notify_new_appointment(
        user_name=current_user.name,
        user_email=current_user.email,
        user_phone=current_user.phone,
        service_name=service.name,
        appointment_time=db_appointment.appointment_time
    )
    
    return db_appointment

@router.put("/{appointment_id}", response_model=AppointmentSchema)
def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем существующую запись
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверяем права доступа
    is_admin = current_user.is_admin
    is_owner = db_appointment.user_id == current_user.id
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Нет доступа к этой записи")
    
    # Обновляем поля записи
    if appointment_update.appointment_time is not None and (is_admin or is_owner):
        service = db.query(Service).filter(Service.id == db_appointment.service_id).first()
        appointment_end_time = appointment_update.appointment_time + timedelta(minutes=service.duration)
        
        # Проверяем доступность нового времени
        overlapping_appointments = db.query(Appointment).filter(
            Appointment.id != appointment_id,
            Appointment.appointment_time < appointment_end_time,
            Appointment.appointment_time + timedelta(minutes=service.duration) > appointment_update.appointment_time,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).all()
        
        if overlapping_appointments:
            raise HTTPException(status_code=400, detail="Выбранное время уже занято")
        
        db_appointment.appointment_time = appointment_update.appointment_time
    
    # Обновление статуса могут делать только админы
    if appointment_update.status is not None and is_admin:
        db_appointment.status = appointment_update.status
    
    # Заметки могут обновлять и клиент, и админ
    if appointment_update.notes is not None:
        db_appointment.notes = appointment_update.notes
    
    db.commit()
    db.refresh(db_appointment)
    notify_appointment_status_change(db_appointment)
    return db_appointment

@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем существующую запись
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверяем права доступа
    is_admin = current_user.is_admin
    is_owner = db_appointment.user_id == current_user.id
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Нет доступа к этой записи")
    
    # Если админ - можно удалить, если клиент - можно только отменить
    if is_admin:
        db.delete(db_appointment)
        db.commit()
        return {"message": "Запись успешно удалена"}
    else:
        db_appointment.status = AppointmentStatus.CANCELLED
        db.commit()
        return {"message": "Запись успешно отменена"}

@router.patch("/{appointment_id}", response_model=AppointmentSchema)
def patch_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Частичное обновление записи (только указанные поля)
    Клиенты могут изменять только заметки и статус (только отмена)
    Администраторы могут изменять все поля
    """
    # Получаем существующую запись
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверяем права доступа
    is_admin = current_user.is_admin
    is_owner = db_appointment.user_id == current_user.id
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Нет доступа к этой записи")
    
    # Сохраняем предыдущий статус для проверки изменений
    previous_status = db_appointment.status
    
    # Обрабатываем обновление
    if appointment_update.appointment_time is not None and is_admin:
        service = db.query(Service).filter(Service.id == db_appointment.service_id).first()
        appointment_end_time = appointment_update.appointment_time + timedelta(minutes=service.duration)
        
        # Проверяем доступность нового времени
        overlapping_appointments = db.query(Appointment).filter(
            Appointment.id != appointment_id,
            Appointment.appointment_time < appointment_end_time,
            Appointment.appointment_time + timedelta(minutes=service.duration) > appointment_update.appointment_time,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).all()
        
        if overlapping_appointments:
            raise HTTPException(status_code=400, detail="Выбранное время уже занято")
        
        db_appointment.appointment_time = appointment_update.appointment_time
    
    # Обновление статуса
    if appointment_update.status is not None:
        # Клиенты могут только отменять свои записи
        if not is_admin and appointment_update.status != AppointmentStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Клиенты могут только отменять записи")
        
        db_appointment.status = appointment_update.status
    
    # Заметки могут обновлять и клиент, и админ
    if appointment_update.notes is not None:
        db_appointment.notes = appointment_update.notes
    
    db.commit()
    db.refresh(db_appointment)
    
    # Проверяем, изменился ли статус
    if previous_status != db_appointment.status:
        # Получаем данные пользователя и услуги для уведомления
        user = db.query(User).filter(User.id == db_appointment.user_id).first()
        service = db.query(Service).filter(Service.id == db_appointment.service_id).first()
        
        # Отправляем уведомление об изменении статуса
        notify_appointment_status_change(
            user_name=user.name,
            user_email=user.email,
            user_phone=user.phone,
            service_name=service.name,
            appointment_time=db_appointment.appointment_time,
            status=db_appointment.status,
            notes=db_appointment.notes
        )
    
    return db_appointment 