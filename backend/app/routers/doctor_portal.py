from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from ..database import get_database

router = APIRouter(prefix="/doctor-portal", tags=["Doctor Portal"])


def _parse_month_range(month: str) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(f"{month}-01T00:00:00+00:00")
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(start.year, start.month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _as_utc_iso(value: str | datetime) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _status_map_to_portal(raw: str) -> str:
    if raw in {"REQUESTED", "APPROVED", "CONFIRMED", "UPCOMING"}:
        return "UPCOMING"
    if raw in {"COMPLETED"}:
        return "COMPLETED"
    if raw in {"CANCELLED"}:
        return "CANCELLED"
    return "UPCOMING"


@router.get("/doctors")
def list_doctors():
    db = get_database()
    rows = list(db.doctors.find({}, {"_id": 0, "id": 1, "name": 1, "specialization": 1}).sort("name", 1))
    return [
        {
            "id": str(item["id"]),
            "name": item["name"],
            "specialty": item["specialization"],
            "email": "",
        }
        for item in rows
    ]


@router.get("/appointments")
def list_appointments(
    mode: str | None = Query(default=None),
    doctorId: str | None = Query(default=None),
    month: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    db = get_database()

    if mode == "availability":
        if not doctorId or not month:
            raise HTTPException(status_code=400, detail="doctorId and month required")
        start, end = _parse_month_range(month)
        docs = list(
            db.doctor_portal_appointments.find(
                {
                    "doctorId": doctorId,
                    "status": "UPCOMING",
                    "appointmentDate": {"$gte": start, "$lt": end},
                },
                {"_id": 0, "appointmentDate": 1},
            )
        )
        return [_as_utc_iso(item["appointmentDate"]) for item in docs]

    if not doctorId:
        raise HTTPException(status_code=400, detail="doctorId required")

    query: dict[str, Any] = {"doctorId": doctorId}
    if status:
        query["status"] = status
    if month:
        start, end = _parse_month_range(month)
        query["appointmentDate"] = {"$gte": start, "$lt": end}

    rows = list(db.doctor_portal_appointments.find(query).sort("appointmentDate", 1))
    out = []
    for item in rows:
        out.append(
            {
                "id": str(item["_id"]),
                "patientName": item.get("patientName", "Patient"),
                "patientEmail": item.get("patientEmail", ""),
                "patientAge": item.get("patientAge", ""),
                "patientGender": item.get("patientGender", ""),
                "appointmentDate": _as_utc_iso(item["appointmentDate"]),
                "status": _status_map_to_portal(item.get("status", "UPCOMING")),
                "doctorId": item.get("doctorId", ""),
                "consultationId": item.get("consultationId"),
                "createdAt": _as_utc_iso(item.get("createdAt", datetime.now(timezone.utc))),
            }
        )
    return out


@router.post("/appointments")
def create_appointment(payload: dict[str, Any]):
    db = get_database()

    appointment_date_raw = payload.get("appointmentDate")
    doctor_id = payload.get("doctorId")
    patient_name = payload.get("patientName")
    patient_email = payload.get("patientEmail")

    if not appointment_date_raw:
        raise HTTPException(status_code=400, detail="Missing required appointment date")
    if not doctor_id:
        raise HTTPException(status_code=400, detail="Missing doctorId")
    if not patient_name or not patient_email:
        raise HTTPException(status_code=400, detail="Missing patient information")

    requested_time = datetime.fromisoformat(str(appointment_date_raw).replace("Z", "+00:00"))
    if requested_time.tzinfo is None:
        requested_time = requested_time.replace(tzinfo=timezone.utc)
    requested_time = requested_time.astimezone(timezone.utc)

    window_minutes = 30
    window_start = requested_time.replace(microsecond=0) - timedelta(minutes=window_minutes)
    window_end = requested_time.replace(microsecond=0) + timedelta(minutes=window_minutes)

    conflict = db.doctor_portal_appointments.find_one(
        {
            "doctorId": str(doctor_id),
            "status": "UPCOMING",
            "appointmentDate": {"$gt": window_start, "$lt": window_end},
        }
    )

    if conflict:
        conflict_time = conflict["appointmentDate"].astimezone(timezone.utc).strftime("%I:%M %p")
        raise HTTPException(
            status_code=409,
            detail=f"Dr. is already booked at {conflict_time}. Appointments must be at least 30 minutes apart.",
        )

    entry = {
        "patientName": patient_name,
        "patientEmail": patient_email,
        "patientAge": payload.get("patientAge", ""),
        "patientGender": payload.get("patientGender", ""),
        "appointmentDate": requested_time,
        "status": "UPCOMING",
        "doctorId": str(doctor_id),
        "consultationId": None,
        "createdAt": datetime.now(timezone.utc),
    }
    result = db.doctor_portal_appointments.insert_one(entry)
    saved = {
        **entry,
        "id": str(result.inserted_id),
        "appointmentDate": _as_utc_iso(entry["appointmentDate"]),
        "createdAt": _as_utc_iso(entry["createdAt"]),
    }
    return {"success": True, "appointment": saved}


@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: str, doctorId: str = Query(...)):
    db = get_database()
    try:
        oid = ObjectId(appointment_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid appointment id") from exc

    item = db.doctor_portal_appointments.find_one({"_id": oid, "doctorId": doctorId})
    if not item:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {
        "id": str(item["_id"]),
        "patientName": item.get("patientName", "Patient"),
        "patientEmail": item.get("patientEmail", ""),
        "patientAge": item.get("patientAge", ""),
        "patientGender": item.get("patientGender", ""),
        "appointmentDate": _as_utc_iso(item["appointmentDate"]),
        "status": _status_map_to_portal(item.get("status", "UPCOMING")),
        "doctorId": item.get("doctorId", ""),
        "consultationId": item.get("consultationId"),
    }


@router.patch("/appointments/{appointment_id}")
def patch_appointment(appointment_id: str, payload: dict[str, Any]):
    db = get_database()
    doctor_id = payload.get("doctorId")
    if not doctor_id:
        raise HTTPException(status_code=400, detail="doctorId required")

    update_payload: dict[str, Any] = {}
    if payload.get("status"):
        update_payload["status"] = payload["status"]
    if payload.get("consultationId"):
        update_payload["consultationId"] = payload["consultationId"]

    try:
        oid = ObjectId(appointment_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid appointment id") from exc

    result = db.doctor_portal_appointments.update_one(
        {"_id": oid, "doctorId": doctor_id},
        {"$set": update_payload},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found or unauthorized")
    return {"success": True}


@router.get("/patients")
def list_consultations(userRole: str = Query(...), userId: str = Query(...)):
    db = get_database()
    if userRole == "DOCTOR":
        query = {"doctorId": userId}
    else:
        query = {"patientUserId": userId}

    rows = list(db.doctor_portal_consultations.find(query).sort("date", -1))
    out = []
    for item in rows:
        out.append(
            {
                "id": str(item["_id"]),
                "name": item.get("name", ""),
                "patientEmail": item.get("patientEmail", ""),
                "age": item.get("age", ""),
                "gender": item.get("gender", ""),
                "bloodGroup": item.get("bloodGroup", ""),
                "note": item.get("note", ""),
                "subjective": item.get("subjective", ""),
                "objective": item.get("objective", ""),
                "assessment": item.get("assessment", ""),
                "plan": item.get("plan", ""),
                "doctorId": item.get("doctorId", ""),
                "patientUserId": item.get("patientUserId"),
                "date": _as_utc_iso(item.get("date", datetime.now(timezone.utc))),
            }
        )
    return out


@router.post("/patients")
def create_consultation(payload: dict[str, Any]):
    db = get_database()

    patient_email = payload.get("patientEmail")
    doctor_id = payload.get("doctorId")
    if not patient_email:
        raise HTTPException(status_code=400, detail="Patient Email is required")
    if not doctor_id:
        raise HTTPException(status_code=400, detail="doctorId required")

    entry = {
        "name": payload.get("name", ""),
        "patientEmail": patient_email,
        "age": payload.get("age", ""),
        "gender": payload.get("gender", ""),
        "bloodGroup": payload.get("bloodGroup", ""),
        "note": payload.get("note", ""),
        "subjective": payload.get("subjective", ""),
        "objective": payload.get("objective", ""),
        "assessment": payload.get("assessment", ""),
        "plan": payload.get("plan", ""),
        "doctorId": doctor_id,
        "patientUserId": payload.get("patientUserId"),
        "date": datetime.now(timezone.utc),
    }
    result = db.doctor_portal_consultations.insert_one(entry)
    return {"success": True, "patient": {"id": str(result.inserted_id), **{k: v for k, v in entry.items() if k != 'date'}, "date": _as_utc_iso(entry["date"])}}


@router.get("/reports")
def list_reports(userRole: str = Query(...), userId: str = Query(...), userEmail: str | None = Query(default=None)):
    db = get_database()
    if userRole == "DOCTOR":
        query = {"doctorId": userId, "isEmergency": True}
    else:
        query = {"patientEmail": userEmail}

    rows = list(db.doctor_portal_reports.find(query).sort("createdAt", -1))
    out = []
    for item in rows:
        out.append(
            {
                "id": str(item["_id"]),
                "patientEmail": item.get("patientEmail", ""),
                "patientName": item.get("patientName", ""),
                "doctorId": item.get("doctorId", ""),
                "aiSummary": item.get("aiSummary", ""),
                "isEmergency": bool(item.get("isEmergency", False)),
                "details": item.get("details", ""),
                "rawText": item.get("rawText", ""),
                "createdAt": _as_utc_iso(item.get("createdAt", datetime.now(timezone.utc))),
                "status": item.get("status", "UNREAD"),
            }
        )
    return out


@router.post("/reports")
def create_report(payload: dict[str, Any]):
    db = get_database()

    entry = {
        "patientEmail": payload.get("patientEmail", ""),
        "patientName": payload.get("patientName", ""),
        "doctorId": payload.get("doctorId", ""),
        "aiSummary": payload.get("aiSummary", ""),
        "isEmergency": bool(payload.get("isEmergency", False)),
        "details": payload.get("details", ""),
        "rawText": payload.get("rawText", ""),
        "createdAt": datetime.now(timezone.utc),
        "status": payload.get("status", "UNREAD"),
    }

    result = db.doctor_portal_reports.insert_one(entry)
    return {"id": str(result.inserted_id)}
