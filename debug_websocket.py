import asyncio
import websockets
import json
import time

async def test_with_detailed_logs():
    """Тест с подробным логированием"""
    print("ДЕТАЛЬНАЯ ДИАГНОСТИКА WEB SOCKET")
    print("="*50)
    
    try:
        print("1. Устанавливаю соединение...")
        websocket = await websockets.connect("ws://localhost:8000/ws/items")
        print("Соединение установлено")
        
        # Даем серверу время обработать подключение
        await asyncio.sleep(0.5)
        
        print("\n2. Пробую получить приветственное сообщение...")
        try:
            welcome = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Получено: {welcome[:100]}...")
            
            # Парсим JSON
            welcome_data = json.loads(welcome)
            print(f"Событие: {welcome_data.get('event')}")
            print(f"Сообщение: {welcome_data.get('message')}")
            
        except asyncio.TimeoutError:
            print("Приветствие не получено за 2 секунды")
        
        print("\n3. Тестирую ping...")
        try:
            await websocket.send("ping")
            print("Ping отправлен")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Ответ: {response}")
            
        except asyncio.TimeoutError:
            print("Нет ответа на ping")
        
        print("\n4. Тестирую status...")
        try:
            await websocket.send("status")
            print("Status запрос отправлен")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Ответ: {response}")
            
        except asyncio.TimeoutError:
            print("Нет ответа на status")
        
        print("\n5. Проверяю соединение...")
        try:
            # Пробуем отправить еще один ping
            await websocket.send("ping")
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Соединение активно: {response[:50]}...")
            
        except asyncio.TimeoutError:
            print("Соединение неактивно")
        
        # Закрываем корректно
        print("\n6. Закрываю соединение...")
        await websocket.close()
        print(" Соединение закрыто корректно")
        
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\nСоединение закрыто с ошибкой: код={e.code}")
        if e.reason:
            print(f"   Причина: {e.reason}")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {type(e).__name__}: {e}")
    
    print("\n" + "="*50)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    asyncio.run(test_with_detailed_logs())