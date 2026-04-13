# app/routers/chat_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.manager import manager
from app.services.chat import UserChatService
import uuid
from app.database.dependencies import get_chat_service

router = APIRouter(tags=["Chat WebSocket"])


@router.websocket("/ws/chat/{user_id}")
async def chat_websocket(
    websocket: WebSocket,
    user_id: uuid.UUID,
    service: UserChatService = Depends(get_chat_service),
):
    await manager.connect(websocket, user_id)

    user_rooms = await service.get_user_rooms(user_id)
    for room in user_rooms:
        manager.join_room(user_id, room.id)

    for room in user_rooms:
        await manager.broadcast_to_room(room.id, {
            "type": "user_online",
            "user_id": str(user_id),
            "room_id": str(room.id),
        }, exclude_user_id=user_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "message":
                room_id = uuid.UUID(data["room_id"])
                content = data["content"]

                if not await service.is_room_member(room_id, user_id):
                    await websocket.send_json({"type": "error", "detail": "not a room member"})
                    continue

                msg = await service.save_message(room_id, user_id, content)

                await manager.broadcast_to_room(room_id, {
                    "type": "message",
                    "id": str(msg.id),
                    "room_id": str(msg.room_id),
                    "sender_id": str(msg.sender_id),
                    "content": msg.message,
                    "created_at": msg.created_at.isoformat(),
                    "is_read": msg.is_read,
                })

            # When a message is sent, also notify who has read it
            elif msg_type == "read":
                room_id = uuid.UUID(data["room_id"])
                await service.mark_messages_read(room_id, user_id)

                await manager.broadcast_to_room(room_id, {
                    "type": "messages_read",
                    "room_id": str(room_id),
                    "read_by": str(user_id),
                }, exclude_user_id=user_id)

            elif msg_type == "presence":
                room_id = uuid.UUID(data["room_id"])
                online_users = list(manager.room_connections.get(str(room_id), set()))
                await websocket.send_json({
                    "type": "presence",
                    "room_id": str(room_id),
                    "online_users": online_users,
                })

    except WebSocketDisconnect:
        user_room_ids = manager.get_user_rooms(user_id)
        manager.disconnect(user_id)

        for room_id_str in user_room_ids:
            await manager.broadcast_to_room(uuid.UUID(room_id_str), {
                "type": "user_offline",
                "user_id": str(user_id),
                "room_id": room_id_str,
            })