import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Patient
from ..schemas import AuthResponse, KycRequest, LoginRequest, PatientOut, VerifyOtpRequest
from ..security import hash_government_id
from ..services.otp_service import generate_otp, validate_otp

router = APIRouter(prefix="/auth", tags=["Auth"])
DEV_MASTER_OTP = os.getenv("DEV_MASTER_OTP", "")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    otp = generate_otp(payload.phone)
    return AuthResponse(message=f"OTP sent (dev only): {otp}")


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    dev_otp_match = bool(DEV_MASTER_OTP) and payload.otp == DEV_MASTER_OTP
    if not dev_otp_match and not validate_otp(payload.phone, payload.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    patient = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if not patient:
        patient = Patient(phone=payload.phone, kyc_verified=False)
        db.add(patient)
        db.commit()
        db.refresh(patient)

    return AuthResponse(
        message="Login successful",
        patient=PatientOut.model_validate(patient),
    )


@router.post("/kyc", response_model=PatientOut)
def complete_kyc(payload: KycRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    govt_id_hash = hash_government_id(payload.govt_id)
    existing = db.query(Patient).filter(Patient.govt_id_hash == govt_id_hash, Patient.id != payload.patient_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="This government ID is already linked to another account")

    patient.name = payload.name
    patient.age = payload.age
    patient.gender = payload.gender
    patient.govt_id_hash = govt_id_hash
    patient.kyc_verified = True
    db.commit()
    db.refresh(patient)

    return PatientOut.model_validate(patient)
