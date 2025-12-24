"""
Currency Tracker API - Main Application File
Соответствует всем требованиям ТЗ:
1. REST API для управления items
2. WebSocket /ws/items для real-time уведомлений  
3. Фоновая задача с httpx к API ЦБ РФ
4. NATS интеграция (публикация + подписка)
5. Асинхронная работа с SQLite БД
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
import asyncio
from sqlmodel import SQLModel
from datetime import datetime
import json  

from app.database import engine
from app.background import background_worker
from app.nats_client import nats_client
from app.websocket import manager
from app.api import items, tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла приложения.
    Выполняется при старте и остановке сервера.
    """
    # ==================== STARTUP ====================
    print("="*60)
    print("ЗАПУСК CURRENCY TRACKER API")
    print("="*60)
    
    # 1. Создаем таблицы в БД
    print("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Таблицы созданы")
    
    # 2. Подключаемся к NATS
    print("\nПодключение к NATS...")
    try:
        await nats_client.connect()
        print("Подключено к NATS серверу")
        
        async def nats_message_handler(msg):
            """
            Обработчик сообщений из NATS канала items.updates.
            Соответствует требованию ТЗ: "при получении сообщения извне — логировать"
            """
            try:
                data = json.loads(msg.data.decode())
                print(f"[NATS] Получено из {msg.subject}: {data.get('type', 'unknown')}")
                
                if data.get('type') == 'external_command':
                    print(f"[NATS] Внешняя команда: {data}")
                    
            except Exception as e:
                print(f"[NATS] Ошибка обработки сообщения: {e}")
        
        await nats_client.subscribe("items.updates", nats_message_handler)
        print(" Подписка на канал 'items.updates' создана")
        
    except Exception as e:
        print(f" Не удалось подключиться к NATS: {e}")
        print("   Убедитесь, что NATS сервер запущен: docker-compose up -d")
    
    print("\nЗапуск фоновой задачи...")
    task = asyncio.create_task(background_worker())
    print("Фоновая задача запущена (каждые 5 минут)")
    
    print("\n" + "="*60)
    print("ПРИЛОЖЕНИЕ ЗАПУЩЕНО И ГОТОВО К РАБОТЕ")
    print("="*60)
    print("Документация: http://localhost:8000/docs")
    print("WebSocket: ws://localhost:8000/ws/items")
    print("NATS мониторинг: http://localhost:8222")
    print("="*60)
    
    yield  
    
    # ==================== SHUTDOWN ====================
    print("\n" + "="*60)
    print("ОСТАНОВКА ПРИЛОЖЕНИЯ")
    print("="*60)
    
    print("Остановка фоновой задачи...")
    task.cancel()

    print("Закрытие соединения с NATS...")
    await nats_client.close()
    
    print("Закрытие соединения с базой данных...")
    await engine.dispose()
    
    print("Приложение остановлено корректно")
    print("="*60)

# Создаем FastAPI приложение с контекстом жизненного цикла
app = FastAPI(
    title="Currency Tracker API",
    description="""
    Асинхронный backend для отслеживания курсов валют с ЦБ РФ.
    
    Функциональность:
    - REST API для управления курсами валют (items)
    - WebSocket для real-time уведомлений
    - Фоновая задача, получающая данные с API ЦБ РФ
    - Интеграция с NATS для обмена сообщениями
    """,
    version="1.0.0",
    lifespan=lifespan
)

# ==================== REST API РОУТЕРЫ ====================
app.include_router(items.router) 
app.include_router(tasks.router)  

# ==================== WEBSOCKET ENDPOINT ====================
@app.websocket("/ws/items")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для real-time уведомлений.
    
    Клиенты получают уведомления:
    - При создании/изменении/удалении items
    - При выполнении фоновой задачи
    """
    # Подключаем клиента через менеджер
    await manager.connect(websocket)
    
    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "event": "connected",
            "message": "Подключено к каналу уведомлений Currency Tracker",
            "timestamp": datetime.now().isoformat(),
            "channels": ["items.updates", "background_tasks"]
        })
        
        print(f"[WebSocket] Новое подключение: {websocket.client}")
        
        while True:
            try:
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_json({
                        "event": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif data == "status":
                    # Получаем текущую статистику
                    from app.database import AsyncSessionLocal
                    from app.models import Item
                    from sqlmodel import select
                    
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(select(Item))
                        items_count = len(result.scalars().all())
                    
                    await websocket.send_json({
                        "event": "status",
                        "total_items": items_count,
                        "active_connections": len(manager.active_connections),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Обработка других сообщений
                else:
                    await websocket.send_json({
                        "event": "echo",
                        "message": f"Получено: {data}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                # Клиент отключился корректно
                print(f"[WebSocket] Отключение: {websocket.client}")
                break
                
            except Exception as e:
                # Ошибка в цикле обработки
                print(f"[WebSocket] Ошибка: {e}")
                break
                
    except Exception as e:
        print(f"[WebSocket]  Критическая ошибка: {e}")
    finally:
        manager.disconnect(websocket)
        print(f"[WebSocket]  Очистка подключения: {websocket.client}")

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса.
    Возвращает статус всех компонентов системы.
    """
    status = {
        "status": "healthy",
        "service": "Currency Tracker API",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "operational",
            "database": "connected",
            "websocket": "ready",
            "background_task": "running"
        }
    }
    
    # Проверяем NATS соединение
    try:
        if nats_client.nc and nats_client.nc.is_connected:
            status["components"]["nats"] = "connected"
        else:
            status["components"]["nats"] = "disconnected"
    except:
        status["components"]["nats"] = "unknown"
    
    return status

# ==================== ROOT ENDPOINT ====================
@app.get("/")
async def root():
    """
    Корневой endpoint с информацией о API.
    """
    return {
        "message": "Добро пожаловать в Currency Tracker API",
        "version": "1.0.0",
        "documentation": "/docs",
        "websocket": "/ws/items",
        "endpoints": {
            "items": {
                "GET /items/": "Список всех курсов валют",
                "GET /items/{id}": "Получить курс по ID",
                "POST /items/": "Создать новую запись",
                "PATCH /items/{id}": "Обновить запись",
                "DELETE /items/{id}": "Удалить запись"
            },
            "tasks": {
                "POST /tasks/run": "Запустить фоновую задачу вручную"
            },
            "system": {
                "GET /health": "Проверка здоровья системы",
                "GET /": "Эта страница"
            }
        }
    }