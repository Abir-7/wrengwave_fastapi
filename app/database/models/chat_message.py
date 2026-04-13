from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
 from app.database.models.chat_room import ChatRoom
 from app.database.models.user import User
 from app.database.models.chat_message_read import ChatMessageRead

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    chat_rooms: Mapped["ChatRoom"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship(back_populates="messages")
    from sqlalchemy import Boolean
    read_by: Mapped[List["ChatMessageRead"]] = relationship(
    back_populates="message",
    cascade="all, delete-orphan",
)