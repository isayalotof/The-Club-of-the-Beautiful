import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from dotenv import load_dotenv

load_dotenv()

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройки хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 схема для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login", auto_error=False)

# Функции для работы с паролями
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Функции для работы с JWT токенами
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request = None, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Подробное логирование
    print("====== AUTH DEBUG ======")
    
    # Пробуем получить токен из разных источников
    cookie_token = None
    if request and "access_token" in request.cookies:
        cookie_token = request.cookies.get("access_token")
        print(f"Found access_token cookie: {cookie_token}")
    
    if token:
        print(f"Found OAuth token: {token}")
    
    # Используем любой доступный токен
    active_token = token or cookie_token
    
    if not active_token:
        print("No token available")
        return None
    
    try:
        # Проверяем формат простого токена
        if active_token.startswith("user_"):
            print(f"Using simple token: {active_token}")
            # Формат: user_ID_TIMESTAMP
            parts = active_token.split("_")
            if len(parts) >= 2:
                user_id = int(parts[1])
                print(f"Extracted user_id: {user_id}")
                
                # Находим пользователя по ID
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    print(f"Found user by ID: {user.email}")
                    return user
                else:
                    print(f"No user found with ID: {user_id}")
            else:
                print("Invalid token format")
        
        # Старый код JWT на всякий случай оставляем
        elif active_token.startswith("Bearer "):
            jwt_token = active_token.replace("Bearer ", "")
            try:
                payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
                if email:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        print(f"Found user by JWT: {user.email}")
                        return user
            except Exception as jwt_error:
                print(f"JWT error: {str(jwt_error)}")
    
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    print("No user authenticated")
    print("========================")
    return None

async def get_current_active_admin(current_user: User = Depends(get_current_user)):
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user 