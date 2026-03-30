import csv
from datetime import datetime
from pathlib import Path

from .database import next_sequence


def _load_doctors_from_csv() -> list[dict]:
    csv_path = Path(__file__).resolve().parents[3] / "doctors_dataset.csv"
    if not csv_path.exists():
        return []

    doctors: list[dict] = []
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            doctors.append(
                {
                    "id": next_sequence("doctor_id"),
                    "name": row["Name"].strip(),
                    "specialization": row["Specialization"].strip(),
                    "experience": int(row["ExperienceYears"]),
                    "fees": float(row["ConsultationFee"]),
                    "rating": 4.5,
                    "bio": (
                        f"{row['Specialization'].strip()} specialist at "
                        f"{row['Hospital'].strip()}, {row['City'].strip()}."
                    ),
                    "hospital": row["Hospital"].strip(),
                    "city": row["City"].strip(),
                    "contact": row["Contact"].strip(),
                }
            )
    return doctors


def seed_data(db) -> None:
    if db.doctors.count_documents({}) == 0:
        doctors = _load_doctors_from_csv()
        if not doctors:
            doctors = [
                {
                    "id": next_sequence("doctor_id"),
                    "name": "Dr. Arjun Mehta",
                    "specialization": "Orthopedic",
                    "experience": 11,
                    "fees": 700,
                    "rating": 4.7,
                    "bio": "Joint and sports injury specialist with focus on minimally invasive treatment.",
                },
                {
                    "id": next_sequence("doctor_id"),
                    "name": "Dr. Sana Qureshi",
                    "specialization": "Dental",
                    "experience": 8,
                    "fees": 500,
                    "rating": 4.5,
                    "bio": "Restorative dentist for preventive and cosmetic oral care.",
                },
                {
                    "id": next_sequence("doctor_id"),
                    "name": "Dr. Ritu Sen",
                    "specialization": "General Medicine",
                    "experience": 14,
                    "fees": 600,
                    "rating": 4.8,
                    "bio": "Primary care physician managing chronic and acute adult conditions.",
                },
                {
                    "id": next_sequence("doctor_id"),
                    "name": "Dr. Abhishek Roy",
                    "specialization": "Dermatology",
                    "experience": 9,
                    "fees": 900,
                    "rating": 4.6,
                    "bio": "Clinical dermatologist focused on eczema, acne, and skin allergy plans.",
                },
                {
                    "id": next_sequence("doctor_id"),
                    "name": "Dr. Priya Sharma",
                    "specialization": "Ophthalmology",
                    "experience": 10,
                    "fees": 800,
                    "rating": 4.7,
                    "bio": "Eye care specialist with expertise in cataract and refractive surgery.",
                },
            ]
        db.doctors.insert_many(doctors)

    if db.patients.count_documents({}) == 0:
        patient_id = next_sequence("patient_id")
        db.patients.insert_one(
            {
                "id": patient_id,
                "name": "Demo Patient",
                "age": 30,
                "gender": "Female",
                "phone": "9999999999",
                "govt_id_hash": "demo_hash_only",
                "kyc_verified": False,
                "created_at": datetime.utcnow(),
            }
        )

        db.medical_records.insert_one(
            {
                "id": next_sequence("record_id"),
                "patient_id": patient_id,
                "doctor_id": 1,
                "date": datetime(2026, 3, 20),
                "diagnosis": "Mild knee inflammation",
                "prescription_url": "sample://prescriptions/knee-plan.pdf",
                "doctor_notes": "Physiotherapy for 2 weeks, ice packs twice daily.",
            }
        )
