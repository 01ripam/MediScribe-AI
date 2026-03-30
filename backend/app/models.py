import enum


class AppointmentStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PatientStatus(str, enum.Enum):
    PENDING = "PENDING"
    ABSENT = "ABSENT"
    DIAGNOSED = "DIAGNOSED"
