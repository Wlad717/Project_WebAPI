from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        print(f"[WebSocket Manager] Начало connect() для {websocket.client}")
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket Manager] Подключение принято. Всего: {len(self.active_connections)}")
        return True

    def disconnect(self, websocket: WebSocket):
        print(f"[WebSocket Manager] disconnect() для {websocket.client}")
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WebSocket Manager] Удален. Осталось: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        print(f"[WebSocket Manager] broadcast: {message.get('event', 'unknown')} "
              f"для {len(self.active_connections)} клиентов")
        
        if not self.active_connections:
            print("[WebSocket Manager] Нет активных подключений!")
            return
        
        disconnected = []
        for i, connection in enumerate(self.active_connections):
            try:
                await connection.send_json(message)
                print(f"[WebSocket Manager] Отправлено клиенту #{i}")
            except Exception as e:
                print(f"[WebSocket Manager] Ошибка отправки клиенту #{i}: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()