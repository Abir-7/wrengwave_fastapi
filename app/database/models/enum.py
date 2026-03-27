import enum
from sqlalchemy import Enum

class UserRole(enum.Enum):
    admin = "admin"
    customer = "customer"
    mechanic = "mechanic"

user_role_enum = Enum(UserRole, name="user_role" )

class BookingStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    arrived = "arrived"
    inspecting = "inspecting"
    canceled = "canceled"
    repairing = "repairing"
    completed = "completed"
    paid = "paid"



booking_status_enum = Enum(BookingStatus, name="booking_status") 