import logging
from datetime import datetime
from typing import Optional

# Настройка логгирования
logger = logging.getLogger(__name__)

def send_email_notification(
    recipient_email: str,
    subject: str,
    message: str
) -> bool:
    """
    Отправляет email-уведомление пользователю.
    
    В данной реализации только логирует сообщение.
    Для рабочей версии нужно добавить интеграцию с SMTP-сервером.
    
    Args:
        recipient_email: Email получателя
        subject: Тема письма
        message: Текст письма
        
    Returns:
        bool: Успешность отправки (всегда True в текущей реализации)
    """
    logger.info(f"Отправка email на {recipient_email}")
    logger.info(f"Тема: {subject}")
    logger.info(f"Сообщение: {message}")
    
    # TODO: Добавить реальную отправку email
    
    return True

def send_sms_notification(
    phone_number: str,
    message: str
) -> bool:
    """
    Отправляет SMS-уведомление пользователю.
    
    В данной реализации только логирует сообщение.
    Для рабочей версии нужно добавить интеграцию с SMS-шлюзом.
    
    Args:
        phone_number: Номер телефона получателя
        message: Текст сообщения
        
    Returns:
        bool: Успешность отправки (всегда True в текущей реализации)
    """
    logger.info(f"Отправка SMS на {phone_number}")
    logger.info(f"Сообщение: {message}")
    
    # TODO: Добавить реальную отправку SMS
    
    return True

def notify_appointment_status_change(
    user_name: str,
    user_email: str,
    user_phone: Optional[str],
    service_name: str,
    appointment_time: datetime,
    status: str,
    notes: Optional[str] = None
) -> None:
    """
    Отправляет уведомление клиенту об изменении статуса записи.
    
    Args:
        user_name: Имя пользователя
        user_email: Email пользователя
        user_phone: Телефон пользователя (опционально)
        service_name: Название услуги
        appointment_time: Время записи
        status: Новый статус записи
        notes: Дополнительные заметки (опционально)
    """
    # Форматируем дату и время записи
    formatted_date = appointment_time.strftime("%d.%m.%Y")
    formatted_time = appointment_time.strftime("%H:%M")
    
    # Определяем текст статуса
    status_text = {
        "PENDING": "ожидает подтверждения",
        "CONFIRMED": "подтверждена",
        "COMPLETED": "выполнена",
        "CANCELLED": "отменена"
    }.get(status, status)
    
    # Формируем сообщение для email
    subject = f"Запись на {service_name} - {status_text}"
    message = f"""
Уважаемый(ая) {user_name}!

Ваша запись на услугу {service_name} на {formatted_date} в {formatted_time} была {status_text}.

"""
    
    if status == "CONFIRMED":
        message += """
Пожалуйста, не забудьте прийти вовремя.
Если у вас изменились планы, вы можете отменить запись в личном кабинете или связаться с нами.
"""
    elif status == "CANCELLED":
        message += """
Вы можете создать новую запись в любое удобное для вас время.
"""
    
    if notes:
        message += f"\nПримечание: {notes}\n"
    
    message += """
С уважением,
Команда салона красоты
"""
    
    # Отправляем email
    send_email_notification(user_email, subject, message)
    
    # Отправляем SMS, если указан телефон
    if user_phone:
        sms_message = f"Запись на {service_name} {formatted_date} в {formatted_time} {status_text}."
        if notes:
            sms_message += f" Примечание: {notes}"
        send_sms_notification(user_phone, sms_message)

def notify_new_appointment(
    user_name: str,
    user_email: str,
    user_phone: Optional[str],
    service_name: str,
    appointment_time: datetime
) -> None:
    """
    Отправляет уведомление о новой записи клиенту и администратору.
    
    Args:
        user_name: Имя пользователя
        user_email: Email пользователя
        user_phone: Телефон пользователя (опционально)
        service_name: Название услуги
        appointment_time: Время записи
    """
    # Уведомляем клиента
    notify_appointment_status_change(
        user_name=user_name,
        user_email=user_email,
        user_phone=user_phone,
        service_name=service_name,
        appointment_time=appointment_time,
        status="PENDING"
    )
    
    # TODO: Уведомить администратора о новой записи 