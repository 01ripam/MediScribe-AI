import shutil
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MedicalRecord, Patient
from ..schemas import RecordOut

router = APIRouter(tags=["Records"])
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/records", response_model=list[RecordOut])
def list_records(patient_id: int = Query(...), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    rows = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).order_by(MedicalRecord.date.desc()).all()
    return [RecordOut.model_validate(r) for r in rows]


@router.post("/records", response_model=RecordOut)
def add_record(
    patient_id: int = Form(...),
    doctor_id: int | None = Form(default=None),
    diagnosis: str = Form(...),
    doctor_notes: str = Form(...),
    record_date: str = Form(...),
    report: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
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
    record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        date=parsed_date,
        diagnosis=diagnosis,
        prescription_url=prescription_url,
        doctor_notes=doctor_notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return RecordOut.model_validate(record)
