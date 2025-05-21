from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Схема базового пользователя
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str

# Схема для создания пользователя
class UserCreate(UserBase):
    password: str

# Схема для обновления пользователя
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

# Схема для ответа с данными пользователя
class User(UserBase):
    id: int
    is_admin: bool = False

    model_config = {"from_attributes": True}

# Схема для авторизации
class UserLogin(BaseModel):
    email: EmailStr
    password: str 