# app/websocket/manager.py
from fastapi import WebSocket
from collections import defaultdict
from typing import Dict, Set
import uuid

class ConnectionManager:
    def __init__(self):
        # user_id (UUID str) -> WebSocket
        self.user_connections: Dict[str, WebSocket] = {}
        # room_id (UUID str) -> set of user_id strings
        self.room_connections: Dict[str, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        await websocket.accept()
        self.user_connections[str(user_id)] = websocket

    def disconnect(self, user_id: uuid.UUID):
        uid = str(user_id)
        self.user_connections.pop(uid, None)
        for members in self.room_connections.values():
            members.discard(uid)

    def join_room(self, user_id: uuid.UUID, room_id: uuid.UUID):
        self.room_connections[str(room_id)].add(str(user_id))

    def leave_room(self, user_id: uuid.UUID, room_id: uuid.UUID):
        self.room_connections[str(room_id)].discard(str(user_id))

    def get_user_rooms(self, user_id: uuid.UUID) -> list[str]:
        uid = str(user_id)
        return [room_id for room_id, members in self.room_connections.items() if uid in members]

    async def send_to_user(self, user_id: uuid.UUID, data: dict):
        ws = self.user_connections.get(str(user_id))
        if ws:
            await ws.send_json(data)

    async def broadcast_to_room(self, room_id: uuid.UUID, data: dict, exclude_user_id: uuid.UUID = None):
        for uid in self.room_connections[str(room_id)]:
            if exclude_user_id and uid == str(exclude_user_id):
                continue
            ws = self.user_connections.get(uid)
            if ws:
                await ws.send_json(data)

    def is_online(self, user_id: uuid.UUID) -> bool:
        return str(user_id) in self.user_connections


manager = ConnectionManager()