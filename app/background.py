import httpx
import asyncio
from datetime import datetime
from app.database import AsyncSessionLocal
from app.models import Item
from sqlmodel import select
from app.websocket import manager
from app.nats_client import nats_client
import json

async def fetch_currency_rates():
    """Получает курсы валют с ЦБ РФ API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.cbr-xml-daily.ru/daily_json.js")
            data = response.json()
            
            # Обрабатываем основные валюты
            currencies_to_track = {
                "USD": "Доллар США",
                "EUR": "Евро", 
                "GBP": "Фунт стерлингов",
                "CNY": "Китайский юань",
                "JPY": "Японская иена",
                "CHF": "Швейцарский франк",
                "CAD": "Канадский доллар",
                "AUD": "Австралийский доллар",
                "TRY": "Турецкая лира",
                "KZT": "Казахстанский тенге",
                "BYN": "Белорусский рубль",
                "UAH": "Украинская гривна",
                "HKD": "Гонконгский доллар",
                "SGD": "Сингапурский доллар"
            }
            
            rates = []
            for code, name in currencies_to_track.items():
                if code in data["Valute"]:
                    valute = data["Valute"][code]
                    rates.append({
                        "currency_code": code,
                        "currency_name": name,
                        "rate": valute["Value"],
                        "nominal": valute["Nominal"]
                    })
            
            return rates
    except Exception as e:
        print(f"Ошибка при получении курсов: {e}")
        return []

async def update_currency_rates():
    """Основная фоновая задача - обновляет курсы валют и сохраняет как Items"""
    print("[Фоновая задача] Получение курсов валют...")
    
    rates = await fetch_currency_rates()
    
    if rates:
        async with AsyncSessionLocal() as db:
            added_count = 0
            
            for rate_data in rates:
                stmt = select(Item).where(
                    Item.code == rate_data["currency_code"],
                    Item.category == "currency"
                ).order_by(Item.timestamp.desc())
                
                result = await db.execute(stmt)

                last_item = result.first()
                
                if not last_item or abs(last_item[0].value - rate_data["rate"]) > 0.001:
                    new_item = Item(
                        name=rate_data["currency_name"],
                        code=rate_data["currency_code"],
                        value=rate_data["rate"],
                        quantity=rate_data["nominal"],
                        category="currency"
                    )
                    db.add(new_item)
                    added_count += 1
                    print(f"   Добавлен курс: {rate_data['currency_code']} = {rate_data['rate']}")
            
            if added_count > 0:
                await db.commit()
                print(f"[Фоновая задача] Добавлено {added_count} items (валют)")
                
                # Отправляем уведомление через WebSocket
                await manager.broadcast({
                    "event": "background_task_completed",
                    "message": f"Добавлено {added_count} валют как items",
                    "timestamp": datetime.now().isoformat(),
                    "items_count": added_count
                })
                
                # Публикуем событие в NATS
                await nats_client.publish("items.updates", {
                    "type": "background_update",
                    "data": {
                        "items_added": added_count,
                        "items": [
                            {
                                "name": rate["currency_name"],
                                "code": rate["currency_code"],
                                "value": rate["rate"]
                            }
                            for rate in rates
                        ]
                    },
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print("[Фоновая задача] Новых курсов не найдено")
    
    return rates

async def background_worker():
    """Бесконечный цикл фоновой задачи"""
    while True:
        try:
            await update_currency_rates()
        except Exception as e:
            print(f"[Фоновая задача] Ошибка: {e}")
        
        await asyncio.sleep(300)  # 5 минут