import shutil
from datetime import date, datetime, time
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from ..database import get_database, next_sequence
from ..schemas import RecordOut

router = APIRouter(tags=["Records"])
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/records", response_model=list[RecordOut])
def list_records(patient_id: int = Query(...)):
    db = get_database()
    patient = db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    rows = list(db.medical_records.find({"patient_id": patient_id}).sort("date", -1))
    out: list[RecordOut] = []
    for row in rows:
        value = row.get("date")
        if isinstance(value, datetime):
            row["date"] = value.date()
        row.pop("_id", None)
        out.append(RecordOut.model_validate(row))
    return out


@router.post("/records", response_model=RecordOut)
def add_record(
    patient_id: int = Form(...),
    doctor_id: int | None = Form(default=None),
    diagnosis: str = Form(...),
    doctor_notes: str = Form(...),
    record_date: str = Form(...),
    report: UploadFile | None = File(default=None),
):
    db = get_database()
    patient = db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    prescription_url = ""
    if report:
        safe_name = f"p{patient_id}_{report.filename}"
        destination = UPLOAD_DIR / safe_name
        with destination.open("wb") as buffer:
            shutil.copyfileobj(report.file, buffer)
        prescription_url = str(destination)

    parsed_date = date.fromisoformat(record_date)
    record = {
        "id": next_sequence("record_id"),
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": datetime.combine(parsed_date, time.min),
        "diagnosis": diagnosis,
        "prescription_url": prescription_url,
        "doctor_notes": doctor_notes,
    }
    db.medical_records.insert_one(record)
    record["date"] = parsed_date
    record.pop("_id", None)
    return RecordOut.model_validate(record)
