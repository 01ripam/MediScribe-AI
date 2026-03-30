import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from ..database import get_database, next_sequence
from ..models import AppointmentStatus, PaymentStatus, PatientStatus
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentPatch
from ..exceptions import (
    AppointmentNotFoundError,
    DoctorNotFoundError,
    PatientNotFoundError,
    KYCNotCompletedError,
    SlotConflictError,
    InvalidAppointmentStatusError,
    DatabaseOperationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Appointments"])
REQUESTED_HOLD_MINUTES = 30


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate):
    """
    Create a new appointment.
    
    Args:
        payload: Appointment creation request
        
    Returns:
        Created appointment details
        
    Raises:
        PatientNotFoundError: If patient doesn't exist
        KYCNotCompletedError: If patient hasn't completed KYC
        DoctorNotFoundError: If doctor doesn't exist
        SlotConflictError: If slot is already booked
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()

        # Verify patient exists and has completed KYC
        patient = db.patients.find_one({"id": payload.patient_id})
        if not patient:
            logger.warning(f"Appointment creation failed: patient {payload.patient_id} not found")
            raise PatientNotFoundError()
        
        if not patient.get("kyc_verified", False):
            logger.warning(f"KYC not completed for patient {payload.patient_id}")
            raise KYCNotCompletedError(required_for="booking appointments")

        # Verify doctor exists
        doctor = db.doctors.find_one({"id": payload.doctor_id})
        if not doctor:
            logger.warning(f"Appointment creation failed: doctor {payload.doctor_id} not found")
            raise DoctorNotFoundError(doctor_id=payload.doctor_id)

        # Release stale requested holds so slots don't remain blocked forever.
        hold_cutoff = datetime.utcnow() - timedelta(minutes=REQUESTED_HOLD_MINUTES)
        db.appointments.update_many(
            {
                "status": AppointmentStatus.REQUESTED.value,
                "payment_status": PaymentStatus.PENDING.value,
                "created_at": {"$lt": hold_cutoff},
            },
            {"$set": {"status": AppointmentStatus.CANCELLED.value}},
        )

        # Auto-cancel any existing REQUESTED appointment for the same patient/doctor.
        # This allows users to change their slot selection without accumulating multiple holds.
        db.appointments.update_many(
            {
                "patient_id": payload.patient_id,
                "doctor_id": payload.doctor_id,
                "status": AppointmentStatus.REQUESTED.value,
            },
            {"$set": {"status": AppointmentStatus.CANCELLED.value}},
        )

        # Check for slot conflicts
        busy_appointment = db.appointments.find_one(
            {
                "doctor_id": payload.doctor_id,
                "slot": payload.slot,
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
                        "created_at": {"$gte": hold_cutoff},
                    },
                ],
            }
        )
        if busy_appointment:
            logger.warning(
                f"Slot conflict: doctor {payload.doctor_id} busy for slot {payload.slot}"
            )
            raise SlotConflictError(
                doctor_id=payload.doctor_id,
                slot=payload.slot,
            )

        # Create appointment
        try:
            appt = {
                "id": next_sequence("appointment_id"),
                "patient_id": payload.patient_id,
                "doctor_id": payload.doctor_id,
                "slot": payload.slot,
                "status": AppointmentStatus.REQUESTED.value,
                "payment_status": PaymentStatus.PENDING.value,
                "payment_reference": None,
                "razorpay_order_id": None,
                                "patient_status": PatientStatus.PENDING.value,
                "created_at": datetime.utcnow(),
            }
            db.appointments.insert_one(appt)
            appt.pop("_id", None)
            
            logger.info(f"Appointment {appt['id']} created for patient {payload.patient_id}")
            return AppointmentOut.model_validate(appt)
        except Exception as e:
            logger.error(f"Failed to insert appointment: {e}")
            raise DatabaseOperationError(
                operation="insert_appointment",
                original_error=e,
            )
            
    except (PatientNotFoundError, KYCNotCompletedError, DoctorNotFoundError, 
            SlotConflictError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Appointment creation failed: {e}")
        raise DatabaseOperationError(
            operation="create_appointment",
            original_error=e,
        )


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    patient_id: int = Query(...),
    status: AppointmentStatus | None = Query(default=None),
):
    """
    List appointments for a patient.
    
    Args:
        patient_id: Patient ID to filter by
        status: Optional appointment status filter
        
    Returns:
        List of appointments
        
    Raises:
        DatabaseOperationError: If database query fails
    """
    try:
        db = get_database()

        query: dict[str, object] = {"patient_id": patient_id}
        if status:
            query["status"] = status.value

        rows = list(db.appointments.find(query).sort("created_at", -1))
        out: list[AppointmentOut] = []
        for item in rows:
            item.pop("_id", None)
            out.append(AppointmentOut.model_validate(item))
        
        logger.info(f"Listed {len(out)} appointments for patient {patient_id}")
        return out
        
    except Exception as e:
        logger.error(f"Failed to list appointments for patient {patient_id}: {e}")
        raise DatabaseOperationError(
            operation="list_appointments",
            original_error=e,
        )


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentPatch):
    """
    Update appointment status.
    
    Args:
        appointment_id: Appointment ID to update
        payload: Update request with action
        
    Returns:
        Updated appointment details
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        InvalidAppointmentStatusError: If action invalid for current status
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Fetch appointment
        appointment = db.appointments.find_one({"id": appointment_id})
        if not appointment:
            logger.warning(f"Appointment {appointment_id} not found")
            raise AppointmentNotFoundError(appointment_id=appointment_id)

        current_status = appointment["status"]

        # Validate and apply action
        if payload.action == "approve":
            if current_status != AppointmentStatus.REQUESTED.value:
                logger.warning(
                    f"Cannot approve appointment {appointment_id} in {current_status} status"
                )
                raise InvalidAppointmentStatusError(
                    current_status=current_status,
                    needed_status=AppointmentStatus.REQUESTED.value,
                )
            try:
                db.appointments.update_one(
                    {"id": appointment_id},
                    {"$set": {"status": AppointmentStatus.APPROVED.value}}
                )
                logger.info(f"Appointment {appointment_id} approved")
            except Exception as e:
                raise DatabaseOperationError(
                    operation="approve_appointment",
                    original_error=e,
                )

        elif payload.action == "pay":
            raise HTTPException(
                status_code=400,
                detail="Use /payments/orders to create payment order and /payments/verify to verify payment",
            )

        elif payload.action == "cancel":
            if current_status == AppointmentStatus.CONFIRMED.value:
                logger.warning(
                    f"Cannot cancel confirmed appointment {appointment_id}"
                )
                raise InvalidAppointmentStatusError(
                    current_status=current_status,
                    needed_status="not CONFIRMED",
                )
            try:
                db.appointments.update_one(
                    {"id": appointment_id},
                    {"$set": {"status": AppointmentStatus.CANCELLED.value}}
                )
                logger.info(f"Appointment {appointment_id} cancelled")
            except Exception as e:
                raise DatabaseOperationError(
                    operation="cancel_appointment",
                    original_error=e,
                )

        # Fetch and return updated appointment
        updated = db.appointments.find_one({"id": appointment_id})
        if not updated:
            raise AppointmentNotFoundError(appointment_id=appointment_id)
        
        updated.pop("_id", None)
        return AppointmentOut.model_validate(updated)
        
    except (AppointmentNotFoundError, InvalidAppointmentStatusError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Appointment update failed: {e}")
        raise DatabaseOperationError(
            operation="update_appointment",
            original_error=e,
        )


@router.post("/appointments/{appointment_id}/reject-and-reassign")
def reject_and_reassign(appointment_id: int, payload: AppointmentCreate):
    """
    Doctor rejects current slot and reassigns patient to a new slot.
    
    Args:
        appointment_id: Appointment ID to reject
        payload: New appointment details (patient_id, doctor_id, slot)
        
    Returns:
        Updated appointment details
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        SlotConflictError: If new slot is already busy
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Fetch current appointment
        appointment = db.appointments.find_one({"id": appointment_id})
        if not appointment:
            logger.warning(f"Appointment {appointment_id} not found for rejection")
            raise AppointmentNotFoundError(appointment_id=appointment_id)
        
        # Cancel old appointment
        db.appointments.update_one(
            {"id": appointment_id},
            {"$set": {"status": AppointmentStatus.CANCELLED.value}},
        )
        logger.info(f"Appointment {appointment_id} rejected by doctor")
        
        # Create new appointment with new slot
        hold_cutoff = datetime.utcnow() - timedelta(minutes=REQUESTED_HOLD_MINUTES)
        db.appointments.update_many(
            {
                "status": AppointmentStatus.REQUESTED.value,
                "payment_status": PaymentStatus.PENDING.value,
                "created_at": {"$lt": hold_cutoff},
            },
            {"$set": {"status": AppointmentStatus.CANCELLED.value}},
        )
        
        # Check for slot conflicts
        busy_appointment = db.appointments.find_one(
            {
                "doctor_id": payload.doctor_id,
                "slot": payload.slot,
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
                        "created_at": {"$gte": hold_cutoff},
                    },
                ],
            }
        )
        if busy_appointment:
            logger.warning(
                f"Slot conflict on reassignment: doctor {payload.doctor_id} busy for slot {payload.slot}"
            )
            raise SlotConflictError(
                doctor_id=payload.doctor_id,
                slot=payload.slot,
            )
        
        # Create new appointment with APPROVED status directly (doctor-assigned)
        try:
            new_appt = {
                "id": next_sequence("appointment_id"),
                "patient_id": payload.patient_id,
                "doctor_id": payload.doctor_id,
                "slot": payload.slot,
                "status": AppointmentStatus.APPROVED.value,
                "payment_status": PaymentStatus.PENDING.value,
                "payment_reference": None,
                "razorpay_order_id": None,
                "patient_status": PatientStatus.PENDING.value,
                "created_at": datetime.utcnow(),
            }
            db.appointments.insert_one(new_appt)
            new_appt.pop("_id", None)
            logger.info(f"New appointment {new_appt['id']} created after rejection of {appointment_id}")
            return AppointmentOut.model_validate(new_appt)
        except Exception as e:
            logger.error(f"Failed to create reassignment appointment: {e}")
            raise DatabaseOperationError(
                operation="create_reassignment_appointment",
                original_error=e,
            )
            
    except (AppointmentNotFoundError, SlotConflictError, DatabaseOperationError):
        raise
    except Exception as e:
        logger.error(f"Reject and reassign failed: {e}")
        raise DatabaseOperationError(
            operation="reject_and_reassign",
            original_error=e,
        )



@router.patch("/appointments/{appointment_id}/patient-status")
def update_patient_status(appointment_id: int, patient_status: PatientStatus):
    """
    Doctor marks patient attendance/diagnosis status.
    
    Args:
        appointment_id: Appointment ID
        patient_status: Status to set (ABSENT or DIAGNOSED)
        
    Returns:
        Updated appointment details
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Fetch appointment
        appointment = db.appointments.find_one({"id": appointment_id})
        if not appointment:
            logger.warning(f"Appointment {appointment_id} not found for status update")
            raise AppointmentNotFoundError(appointment_id=appointment_id)
        
        # Update patient status
        try:
            db.appointments.update_one(
                {"id": appointment_id},
                {"$set": {"patient_status": patient_status.value}}
            )
            logger.info(f"Appointment {appointment_id} patient status updated to {patient_status.value}")
        except Exception as e:
            raise DatabaseOperationError(
                operation="update_patient_status",
                original_error=e,
            )
        
        # Fetch and return updated appointment
        updated = db.appointments.find_one({"id": appointment_id})
        if not updated:
            raise AppointmentNotFoundError(appointment_id=appointment_id)
        
        updated.pop("_id", None)
        return AppointmentOut.model_validate(updated)
        
    except (AppointmentNotFoundError, DatabaseOperationError):
        raise
    except Exception as e:
        logger.error(f"Patient status update failed: {e}")
        raise DatabaseOperationError(
            operation="update_patient_status",
            original_error=e,
        )
