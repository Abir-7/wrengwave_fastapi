# app/database/models/chat_message_read.py
from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.database.models.chat_message import ChatMessage
    from app.database.models.user import User

class ChatMessageRead(BaseModel):
    __tablename__ = "chat_message_reads"

    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message: Mapped["ChatMessage"] = relationship(back_populates="read_by")
    user: Mapped["User"] = relationship(back_populates="message_reads")