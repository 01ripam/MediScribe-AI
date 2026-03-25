from datetime import date

from sqlalchemy.orm import Session

from .models import Doctor, MedicalRecord, Patient


def seed_data(db: Session) -> None:
    if db.query(Doctor).count() == 0:
        doctors = [
            Doctor(
                name="Dr. Arjun Mehta",
                specialization="Orthopedic",
                experience=11,
                fees=700,
                rating=4.7,
                bio="Joint and sports injury specialist with focus on minimally invasive treatment.",
            ),
            Doctor(
                name="Dr. Sana Qureshi",
                specialization="Dental",
                experience=8,
                fees=500,
                rating=4.5,
                bio="Restorative dentist for preventive and cosmetic oral care.",
            ),
            Doctor(
                name="Dr. Ritu Sen",
                specialization="General Medicine",
                experience=14,
                fees=600,
                rating=4.8,
                bio="Primary care physician managing chronic and acute adult conditions.",
            ),
            Doctor(
                name="Dr. Abhishek Roy",
                specialization="Dermatology",
                experience=9,
                fees=900,
                rating=4.6,
                bio="Clinical dermatologist focused on eczema, acne, and skin allergy plans.",
            ),
        ]
        db.add_all(doctors)
        db.commit()

    if db.query(Patient).count() == 0:
        patient = Patient(
            name="Demo Patient",
            age=30,
            gender="Female",
            phone="9999999999",
            govt_id_hash="demo_hash_only",
            kyc_verified=True,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        sample_record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=1,
            date=date(2026, 3, 20),
            diagnosis="Mild knee inflammation",
            prescription_url="sample://prescriptions/knee-plan.pdf",
            doctor_notes="Physiotherapy for 2 weeks, ice packs twice daily.",
        )
        db.add(sample_record)
        db.commit()
