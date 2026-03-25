from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Doctor
from ..schemas import DoctorOut, SymptomRequest, SymptomSuggestion
from ..services.symptom_service import suggest_specialization

router = APIRouter(tags=["Doctors"])


def _build_slots(doctor_id: int) -> list[str]:
    base = ["10:00 AM", "11:00 AM", "02:00 PM", "05:00 PM"]
    return [f"2026-03-{(doctor_id % 7) + 25} {slot}" for slot in base]


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(
    specialization: str | None = Query(default=None),
    name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if name:
        query = query.filter(Doctor.name.ilike(f"%{name}%"))

    doctors = query.order_by(Doctor.rating.desc()).all()
    return [
        DoctorOut(
            id=d.id,
            name=d.name,
            specialization=d.specialization,
            experience=d.experience,
            fees=d.fees,
            rating=d.rating,
            bio=d.bio,
            available_slots=_build_slots(d.id),
        )
        for d in doctors
    ]


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return DoctorOut(
        id=doctor.id,
        name=doctor.name,
        specialization=doctor.specialization,
        experience=doctor.experience,
        fees=doctor.fees,
        rating=doctor.rating,
        bio=doctor.bio,
        available_slots=_build_slots(doctor.id),
    )


@router.post("/ai/symptom-suggestion", response_model=SymptomSuggestion)
def symptom_suggestion(payload: SymptomRequest):
    suggestion, specialization = suggest_specialization(payload.symptoms)
    return SymptomSuggestion(suggestion=suggestion, specialization=specialization)
