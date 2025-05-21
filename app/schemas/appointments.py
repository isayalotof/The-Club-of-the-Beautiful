from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.appointments import AppointmentStatus
from app.schemas.users import User
from app.schemas.services import Service

# Схема базовой записи
class AppointmentBase(BaseModel):
    service_id: int
    appointment_time: datetime
    notes: Optional[str] = None

# Схема для создания записи
class AppointmentCreate(AppointmentBase):
    pass

# Схема для обновления записи
class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

# Схема для ответа с данными записи
class Appointment(AppointmentBase):
    id: int
    user_id: int
    status: AppointmentStatus
    created_at: datetime

    model_config = {"from_attributes": True}

# Расширенная схема записи с информацией о пользователе и услуге
class AppointmentDetail(Appointment):
    user: User
    service: Service

# Схема для списка записей
class AppointmentList(BaseModel):
    appointments: List[AppointmentDetail]
    total: int 