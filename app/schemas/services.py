from pydantic import BaseModel
from typing import Optional, List

# Схема базовой услуги
class ServiceBase(BaseModel):
    name: str
    description: str
    price: float
    duration: int
    category: str
    image_url: Optional[str] = None

# Схема для создания услуги
class ServiceCreate(ServiceBase):
    pass

# Схема для обновления услуги
class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

# Схема для ответа с данными услуги
class Service(ServiceBase):
    id: int

    model_config = {"from_attributes": True}

# Схема для списка услуг
class ServiceList(BaseModel):
    services: List[Service]
    total: int 