from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from ..database import get_database
from ..models import AppointmentStatus
from ..schemas import DoctorOut, SymptomRequest, SymptomSuggestion
from ..services.symptom_service import suggest_specialization

router = APIRouter(tags=["Doctors"])
REQUESTED_HOLD_MINUTES = 30


def _active_busy_filter(doctor_id: int) -> dict:
    cutoff = datetime.utcnow() - timedelta(minutes=REQUESTED_HOLD_MINUTES)
    return {
        "doctor_id": doctor_id,
        "$or": [
            {
                "status": {
                    "$in": [
                        AppointmentStatus.APPROVED.value,
                        AppointmentStatus.CONFIRMED.value,
                    ]
                }
            },
            {
                "status": AppointmentStatus.REQUESTED.value,
                "created_at": {"$gte": cutoff},
            },
        ],
    }


def _build_slots() -> list[str]:
    base = ["10:00 AM", "11:00 AM", "02:00 PM", "05:00 PM"]
    today = date.today()
    slots: list[str] = []
    for day_offset in range(0, 7):
        day_str = (today + timedelta(days=day_offset)).isoformat()
        for time_str in base:
            slots.append(f"{day_str} {time_str}")
    return slots


def _doctor_out(doc: dict, busy_slots: list[str]) -> DoctorOut:
    all_slots = _build_slots()
    busy_set = set(busy_slots)
    free_slots = [slot for slot in all_slots if slot not in busy_set]
    doc.pop("_id", None)
    return DoctorOut(
        id=doc["id"],
        name=doc["name"],
        specialization=doc["specialization"],
        experience=doc["experience"],
        fees=doc["fees"],
        rating=doc["rating"],
        bio=doc.get("bio", ""),
        available_slots=free_slots,
        busy_slots=busy_slots,
    )


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(
    specialization: str | None = Query(default=None),
    name: str | None = Query(default=None),
):
    db = get_database()
    query: dict[str, object] = {}
    if specialization:
        query["specialization"] = {"$regex": specialization, "$options": "i"}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    doctors = list(db.doctors.find(query).sort("rating", -1))
    rows: list[DoctorOut] = []
    for doc in doctors:
        busy = db.appointments.find(
            _active_busy_filter(doc["id"]),
            {"slot": 1, "_id": 0},
        )
        busy_slots = sorted({row["slot"] for row in busy})
        rows.append(_doctor_out(doc, busy_slots))
    return rows


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int):
    db = get_database()
    doctor = db.doctors.find_one({"id": doctor_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    busy = db.appointments.find(_active_busy_filter(doctor_id), {"slot": 1, "_id": 0})
    busy_slots = sorted({row["slot"] for row in busy})
    return _doctor_out(doctor, busy_slots)


@router.post("/ai/symptom-suggestion", response_model=SymptomSuggestion)
def symptom_suggestion(payload: SymptomRequest):
    suggestion, specialization = suggest_specialization(payload.symptoms)
    return SymptomSuggestion(suggestion=suggestion, specialization=specialization)
