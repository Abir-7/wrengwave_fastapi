from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship


from typing import Optional,  Dict,TYPE_CHECKING
from sqlalchemy.dialects.postgresql import JSONB,UUID
from sqlalchemy import ForeignKey 
from sqlalchemy import String, Boolean
import uuid
if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.service_booking import CarBookingService
class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_booking_services.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False,default=False)
    message: Mapped[str] = mapped_column(String)