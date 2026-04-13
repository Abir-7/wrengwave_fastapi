# app/routers/chat_rest.py
from fastapi import APIRouter, Depends
from app.services.chat import UserChatService
from pydantic import BaseModel as PydanticBase
import uuid
from app.database.dependencies import get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


class DMRequest(PydanticBase):
    user_a: uuid.UUID
    user_b: uuid.UUID


class GroupRequest(PydanticBase):
    name: str
    member_ids: list[uuid.UUID]


@router.post("/dm")
async def create_dm(body: DMRequest, service: UserChatService = Depends(get_chat_service)):
    room = await service.get_or_create_dm_room(body.user_a, body.user_b)
    return {"room_id": str(room.id), "is_dm": room.is_dm}


@router.post("/group")
async def create_group(body: GroupRequest, service: UserChatService = Depends(get_chat_service)):
    room = await service.create_group_room(body.name, body.member_ids)
    return {"room_id": str(room.id), "name": room.name}


@router.get("/rooms/{user_id}")
async def list_user_rooms(user_id: uuid.UUID, service: UserChatService = Depends(get_chat_service)):
    rooms = await service.get_user_rooms(user_id)
    return [{"room_id": str(r.id), "name": r.name, "is_dm": r.is_dm} for r in rooms]


@router.get("/messages/{room_id}")
async def list_messages(room_id: uuid.UUID, limit: int = 50, service: UserChatService = Depends(get_chat_service)):
    messages = await service.get_room_messages(room_id, limit)
    return [
        {
            "id": str(m.id),
            "sender_id": str(m.sender_id),
            "content": m.message,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.get("/messages/{message_id}/reads")
async def get_read_status(message_id: uuid.UUID, service: UserChatService = Depends(get_chat_service)):
    reads = await service.get_message_read_status(message_id)
    return [
        {
            "user_id": str(r.user_id),
            "read_at": r.read_at.isoformat(),
        }
        for r in reads
    ]


@router.get("/rooms/{room_id}/unread/{user_id}")
async def get_unread_count(
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    service: UserChatService = Depends(get_chat_service)
):
    count = await service.get_unread_count(room_id, user_id)
    return {"unread_count": count}