from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from typing import List
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.database.models.chat_room_members import ChatRoomMember
    from app.database.models.chat_message import ChatMessage

class ChatRoom(BaseModel):
    __tablename__ = "chat_rooms"
    is_dm: Mapped[bool] = mapped_column(Boolean, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    members: Mapped[List["ChatRoomMember"]] = relationship(back_populates="chat_rooms")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="chat_rooms")