import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from app.database import Base, engine
from app.utils.jinja_filters import setup_jinja2_extensions
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import traceback

# Создаем необходимые директории, если они не существуют
os.makedirs("app/static/uploads/services", exist_ok=True)
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/static/images", exist_ok=True)

# Создаем экземпляр приложения
app = FastAPI(title="Салон красоты", description="API для салона красоты и СПА")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обработка исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Глобальная ошибка: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Добавляем middleware для отладки запросов
@app.middleware("http")
async def debug_request_middleware(request: Request, call_next):
    print(f"\n--- НОВЫЙ ЗАПРОС: {request.method} {request.url.path} ---")
    print(f"Cookies: {request.cookies}")
    
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        print(f"Статус ответа: {response.status_code}")
        print(f"Время обработки: {process_time:.4f} sec")
        print(f"Заголовки ответа: {dict(response.headers)}")
        print("--- ЗАПРОС ЗАВЕРШЕН ---\n")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        print(f"Ошибка при обработке запроса: {str(e)}")
        print(f"Время до ошибки: {process_time:.4f} sec")
        print("--- ЗАПРОС ЗАВЕРШЕН С ОШИБКОЙ ---\n")
        raise

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонизатора
templates = Jinja2Templates(directory="app/templates")
setup_jinja2_extensions(templates)

# Импортируем маршруты (после создания шаблонизатора)
from app.api import appointments, services, users, reviews
from app.web_routes import router as web_router
from app.admin_routes import router as admin_router

# Подключаем маршруты API с проверкой
print("Подключение API маршрутов...")
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])

# Подключаем веб-маршруты с проверкой
print("Подключение веб-маршрутов...")
app.include_router(web_router)

# Подключаем маршруты админ-панели с проверкой
print("Подключение маршрутов админ-панели...")
app.include_router(admin_router)

# Простой тестовый маршрут
@app.get("/test")
async def test_route():
    return {"status": "ok", "message": "API работает"}

# Дополнительный маршрут для проверки состояния аутентификации
@app.get("/auth-status")
async def auth_status(request: Request):
    return {
        "authenticated": "access_token" in request.cookies,
        "cookies": {k: "***" for k in request.cookies.keys()},
    }

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

print(f"Маршруты FastAPI: {[route.path for route in app.routes]}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 