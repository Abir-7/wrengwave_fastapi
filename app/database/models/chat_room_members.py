from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.chat_room import ChatRoom
class ChatRoomMember(BaseModel):
    __tablename__ = "chat_room_members"
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    chat_rooms: Mapped["ChatRoom"] = relationship(back_populates="members")  # note: "members" not "users"
    user: Mapped["User"] = relationship(back_populates="chat_rooms")
