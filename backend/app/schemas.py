from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from .models import AppointmentStatus, PaymentStatus


class LoginRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15)


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str = Field(min_length=4, max_length=6)


class KycRequest(BaseModel):
    patient_id: int
    name: str
    age: int
    gender: str
    govt_id: str = Field(min_length=6, max_length=32)
    govt_id_type: Literal["AADHAAR", "PAN", "VOTER_ID", "OTHER"]


class PatientOut(BaseModel):
    id: int
    name: str | None
    age: int | None
    gender: str | None
    phone: str
    govt_id_hash: str | None
    kyc_verified: bool

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    patient: PatientOut | None = None


class DoctorOut(BaseModel):
    id: int
    name: str
    specialization: str
    experience: int
    fees: float
    rating: float
    bio: str
    available_slots: list[str] = []

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    slot: str


class AppointmentPatch(BaseModel):
    action: Literal["approve", "pay", "cancel"]


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    slot: str
    status: AppointmentStatus
    payment_status: PaymentStatus
    payment_reference: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RecordOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int | None
    date: date
    diagnosis: str
    prescription_url: str
    doctor_notes: str

    class Config:
        from_attributes = True


class SymptomRequest(BaseModel):
    symptoms: list[str]


class SymptomSuggestion(BaseModel):
    suggestion: str
    specialization: str
