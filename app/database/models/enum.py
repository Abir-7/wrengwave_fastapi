import enum
class UserRole(enum.Enum):
    admin = "admin"
    customer = "customer"
    mechanic = "mechanic"

class BookingStatus(enum.Enum):
    pending = "pending"
    arrived = "arrived"
    inspecting = "inspecting"
    canceled = "canceled"
    repairing = "repairing"
    completed = "completed"
    paid = "paid"
