from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime  

from app.database import get_db
from app.models import Item
from app.schemas import ItemResponse, ItemCreate, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=List[ItemResponse])
async def get_items(db: AsyncSession = Depends(get_db)):
    """Получить список всех items"""
    result = await db.execute(select(Item))
    items = result.scalars().all()
    return items

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Получить item по ID"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item

@router.get("/code/{code}", response_model=ItemResponse)
async def get_item_by_code(code: str, db: AsyncSession = Depends(get_db)):
    """Получить последний курс валюты по коду (USD, EUR, etc)"""
    # Получаем последнюю запись для указанного кода валюты
    stmt = select(Item).where(
        Item.code == code.upper()
    ).order_by(Item.timestamp.desc())
    
    result = await db.execute(stmt)
    item = result.first()  # Берем первую (последнюю по времени) запись
    
    if not item:
        raise HTTPException(
            status_code=404, 
            detail=f"Currency with code '{code}' not found"
        )
    
    return item[0]

@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый item"""
    new_item = Item(**item.dict())
    db.add(new_item)
    await db.commit() 
    await db.refresh(new_item)  
    
    from app.websocket import manager
    from app.nats_client import nats_client
    from datetime import datetime
    
    # Уведомление через WebSocket
    await manager.broadcast({
        "event": "item_created", 
        "item_id": new_item.id,
        "name": new_item.name,
        "value": new_item.value,
        "timestamp": datetime.now().isoformat()
    })
    
    # Публикация в NATS
    await nats_client.publish("items.updates", {
        "type": "item_created",
        "data": {
            "id": new_item.id,
            "name": new_item.name,
            "code": new_item.code,
            "value": new_item.value
        },
        "timestamp": datetime.now().isoformat()
    })
    
    return new_item

@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_update: ItemUpdate, db: AsyncSession = Depends(get_db)):
    """Частично обновить item"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Обновляем только переданные поля
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    await db.commit()
    await db.refresh(item)
    
    # Уведомления
    from app.websocket import manager
    from app.nats_client import nats_client
    
    await manager.broadcast({
        "event": "item_updated",
        "item_id": item.id,
        "name": item.name,
        "value": item.value,
        "timestamp": datetime.now().isoformat()
    })
    
    await nats_client.publish("items.updates", {
        "type": "item_updated",
        "data": {
            "id": item.id,
            "name": item.name,
            "value": item.value
        },
        "timestamp": datetime.now().isoformat()
    })
    
    return item

@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить item"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    await db.commit()
    
    # Уведомления
    from app.websocket import manager
    from app.nats_client import nats_client
    
    await manager.broadcast({
        "event": "item_deleted",
        "item_id": item_id,
        "timestamp": datetime.now().isoformat()
    })
    
    await nats_client.publish("items.updates", {
        "type": "item_deleted",
        "data": {"id": item_id},
        "timestamp": datetime.now().isoformat()
    })