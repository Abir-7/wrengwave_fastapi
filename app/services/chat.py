# app/services/chat.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, func
from app.database.models.chat_room import ChatRoom
from app.database.models.chat_room_members import ChatRoomMember
from app.database.models.chat_message import ChatMessage
import uuid
from app.database.models.chat_message_read import ChatMessageRead
from datetime import datetime, timezone
class UserChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_dm_room(self, user_a: uuid.UUID, user_b: uuid.UUID) -> ChatRoom:
        stmt = (
            select(ChatRoom)
            .join(ChatRoomMember, ChatRoomMember.room_id == ChatRoom.id)
            .where(
                and_(
                    ChatRoom.is_dm == True,
                    ChatRoomMember.user_id.in_([user_a, user_b])
                )
            )
            .group_by(ChatRoom.id)
            .having(func.count(ChatRoomMember.user_id) == 2)
        )
        result = await self.db.execute(stmt)
        room = result.scalar_one_or_none()
        if room:
            return room

        room = ChatRoom(is_dm=True, name="dm")
        self.db.add(room)
        await self.db.flush()

        self.db.add_all([
            ChatRoomMember(room_id=room.id, user_id=user_a),
            ChatRoomMember(room_id=room.id, user_id=user_b),
        ])
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def create_group_room(self, name: str, member_ids: list[uuid.UUID]) -> ChatRoom:
        room = ChatRoom(is_dm=False, name=name)
        self.db.add(room)
        await self.db.flush()

        self.db.add_all([
            ChatRoomMember(room_id=room.id, user_id=uid)
            for uid in member_ids
        ])
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def save_message(self, room_id: uuid.UUID, sender_id: uuid.UUID, message: str) -> ChatMessage:
        msg = ChatMessage(room_id=room_id, sender_id=sender_id, message=message)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_room_messages(self, room_id: uuid.UUID, limit: int = 50) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_rooms(self, user_id: uuid.UUID) -> list[ChatRoom]:
        stmt = (
            select(ChatRoom)
            .join(ChatRoomMember, ChatRoomMember.room_id == ChatRoom.id)
            .where(ChatRoomMember.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def is_room_member(self, room_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(ChatRoomMember).where(
            and_(
                ChatRoomMember.room_id == room_id,
                ChatRoomMember.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_messages_read(self, room_id: uuid.UUID, user_id: uuid.UUID):
        # Get all messages in room not yet read by this user
        already_read_subq = (
            select(ChatMessageRead.message_id)
            .where(ChatMessageRead.user_id == user_id)
        )
        stmt = (
            select(ChatMessage)
            .where(
                and_(
                    ChatMessage.room_id == room_id,
                    ChatMessage.sender_id != user_id,
                    ChatMessage.id.not_in(already_read_subq),
                )
            )
        )
        result = await self.db.execute(stmt)
        unread_messages = result.scalars().all()

        if not unread_messages:
            return

        self.db.add_all([
            ChatMessageRead(
                message_id=msg.id,
                user_id=user_id,
                read_at=datetime.now(timezone.utc),
            )
            for msg in unread_messages
        ])
        await self.db.commit()

    async def get_message_read_status(self, message_id: uuid.UUID) -> list[ChatMessageRead]:
        """Who has read a specific message"""
        stmt = select(ChatMessageRead).where(ChatMessageRead.message_id == message_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_unread_count(self, room_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """How many unread messages in a room for this user"""
        already_read_subq = (
            select(ChatMessageRead.message_id)
            .where(ChatMessageRead.user_id == user_id)
        )
        stmt = (
            select(func.count())
            .select_from(ChatMessage)
            .where(
                and_(
                    ChatMessage.room_id == room_id,
                    ChatMessage.sender_id != user_id,
                    ChatMessage.id.not_in(already_read_subq),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar()