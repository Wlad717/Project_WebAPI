import nats
import json
from typing import Optional, Callable

class NATSClient:
    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        
    async def connect(self, servers="nats://localhost:4222"):
        self.nc = await nats.connect(servers)
        return self.nc
    
    async def publish(self, subject: str, message: dict):
        if self.nc:
            await self.nc.publish(subject, json.dumps(message).encode())
            print(f"[NATS] Опубликовано в {subject}: {message.get('type', 'unknown')}")
    
    async def subscribe(self, subject: str, callback: Callable):
        """Подписка на канал NATS"""
        if self.nc:
            sub = await self.nc.subscribe(subject, cb=callback)
            print(f"[NATS] Подписка на {subject} создана")
            return sub
    
    async def close(self):
        if self.nc:
            await self.nc.close()

nats_client = NATSClient()