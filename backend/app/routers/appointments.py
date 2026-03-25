from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Appointment, AppointmentStatus, Doctor, Patient, PaymentStatus
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentPatch
from ..services.payment_service import simulate_razorpay_payment

router = APIRouter(tags=["Appointments"])


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.kyc_verified:
        raise HTTPException(status_code=403, detail="Complete KYC before booking appointments")

    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    appt = Appointment(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        slot=payload.slot,
        status=AppointmentStatus.REQUESTED,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return AppointmentOut.model_validate(appt)


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    patient_id: int = Query(...),
    status: AppointmentStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment).filter(Appointment.patient_id == patient_id)
    if status:
        query = query.filter(Appointment.status == status)
    rows = query.order_by(Appointment.created_at.desc()).all()
    return [AppointmentOut.model_validate(a) for a in rows]


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentPatch, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if payload.action == "approve":
        if appointment.status != AppointmentStatus.REQUESTED:
            raise HTTPException(status_code=400, detail="Only REQUESTED appointments can be approved")
        appointment.status = AppointmentStatus.APPROVED

    elif payload.action == "pay":
        if appointment.status != AppointmentStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Payment allowed only for APPROVED appointments")
        success, reference = simulate_razorpay_payment(appointment.id)
        appointment.payment_reference = reference
        if success:
            appointment.payment_status = PaymentStatus.SUCCESS
            appointment.status = AppointmentStatus.CONFIRMED
        else:
            appointment.payment_status = PaymentStatus.FAILED

    elif payload.action == "cancel":
        if appointment.status == AppointmentStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Confirmed appointments cannot be cancelled in this flow")
        appointment.status = AppointmentStatus.CANCELLED

    db.commit()
    db.refresh(appointment)
    return AppointmentOut.model_validate(appointment)
