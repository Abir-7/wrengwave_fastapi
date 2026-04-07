import enum
from sqlalchemy import Enum

class UserRole(str,enum.Enum):
    admin = "admin"
    customer = "customer"
    mechanic = "mechanic"

user_role_enum = Enum(UserRole, name="user_role" )

class BookingStatus(str,enum.Enum):
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


class PaymentStatus(str,enum.Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    REFUNDED = "refunded"
    HOLD = "hold"
    PROCESSING = "processing"  
    CANCELLED  = "cancelled"   
    DISPUTED   = "disputed"    

payment_status_enum = Enum(PaymentStatus, name="payment_status") 