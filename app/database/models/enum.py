from sqlalchemy import Enum
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    customer = "customer"
    mechanic = "mechanic"

user_role_enum = Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x])


class BookingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    arrived = "arrived"
    inspecting = "inspecting"
    canceled = "canceled"
    repairing = "repairing"
    completed = "completed"
    paid = "paid"

booking_status_enum = Enum(BookingStatus, name="booking_status", values_callable=lambda x: [e.value for e in x])


class PaymentStatus(str, enum.Enum):
    PAID               = "paid"
    UNPAID             = "unpaid"
    REFUNDED           = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    HOLD               = "hold"
    PROCESSING         = "processing"
    CANCELLED          = "cancelled"
    DISPUTED           = "disputed"
    FAILED             = "failed"

payment_status_enum = Enum(PaymentStatus, name="payment_status", values_callable=lambda x: [e.value for e in x])