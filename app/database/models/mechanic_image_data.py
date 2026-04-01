from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean

from typing import Optional,  Dict,TYPE_CHECKING
from sqlalchemy.dialects.postgresql import JSONB,UUID
from app.database.models.mechanic_data import MechanicData
import uuid
from sqlalchemy import ForeignKey 

if TYPE_CHECKING:
    from app.database.models.user import User

class MechanicImageData(BaseModel):
    __tablename__ = "mechanic_image_data"

    national_image_id: Mapped[Optional[str]] = mapped_column(String)
    national_id_image_url: Mapped[Optional[str]] = mapped_column(String)
    certificates: Mapped[Optional[Dict]] = mapped_column(JSONB)
    is_linked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=False,default=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="mechanic_image_data")