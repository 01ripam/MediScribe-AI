import os
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from ..database import get_database, next_sequence
from ..schemas import AuthResponse, KycRequest, LoginRequest, PatientOut, VerifyOtpRequest
from ..security import hash_government_id
from ..services.otp_service import generate_otp, validate_otp
from ..exceptions import (
    InvalidOTPError,
    PatientNotFoundError,
    KYCNotCompletedError,
    DuplicateGovernmentIDError,
    DatabaseOperationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])
DEV_MASTER_OTP = os.getenv("DEV_MASTER_OTP", "")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    """
    Initiate login by sending OTP to phone number.
    
    Args:
        payload: Login request with phone number
        
    Returns:
        AuthResponse with OTP (dev only)
        
    Raises:
        DatabaseOperationError: If database operations fail
    """
    try:
        otp = generate_otp(payload.phone)
        logger.info(f"OTP generated for phone: {payload.phone[:3]}****{payload.phone[-2:]}")
        return AuthResponse(message=f"OTP sent (dev only): {otp}")
    except Exception as e:
        logger.error(f"Login failed for phone {payload.phone}: {e}")
        raise DatabaseOperationError(
            operation="login",
            original_error=e,
        )


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp_endpoint(payload: VerifyOtpRequest):
    """
    Verify OTP and create/retrieve patient account.
    
    Args:
        payload: OTP verification request
        
    Returns:
        AuthResponse with patient details
        
    Raises:
        InvalidOTPError: If OTP is invalid or expired
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Check if OTP is valid
        dev_otp_match = bool(DEV_MASTER_OTP) and payload.otp == DEV_MASTER_OTP
        if not dev_otp_match and not validate_otp(payload.phone, payload.otp):
            logger.warning(
                f"Invalid OTP attempt for phone: {payload.phone[:3]}****{payload.phone[-2:]}"
            )
            raise InvalidOTPError("Invalid or expired OTP")
        
        # Find or create patient
        patient = db.patients.find_one({"phone": payload.phone})
        if not patient:
            try:
                patient = {
                    "id": next_sequence("patient_id"),
                    "name": None,
                    "age": None,
                    "gender": None,
                    "phone": payload.phone,
                    "govt_id_hash": None,
                    "kyc_verified": False,
                    "created_at": datetime.utcnow(),
                }
                db.patients.insert_one(patient)
                logger.info(f"New patient created with ID: {patient['id']}")
            except Exception as e:
                logger.error(f"Failed to create patient for phone {payload.phone}: {e}")
                raise DatabaseOperationError(
                    operation="create_patient",
                    original_error=e,
                )
        
        patient.pop("_id", None)
        
        logger.info(f"Patient {patient['id']} verified successfully")
        return AuthResponse(
            message="Login successful",
            patient=PatientOut.model_validate(patient),
        )
        
    except InvalidOTPError:
        # Re-raise OTP errors
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise


@router.post("/kyc", response_model=PatientOut)
def complete_kyc(payload: KycRequest):
    """
    Complete KYC verification for patient.
    
    Args:
        payload: KYC request with patient info and government ID
        
    Returns:
        Updated patient profile
        
    Raises:
        PatientNotFoundError: If patient doesn't exist
        DuplicateGovernmentIDError: If government ID already linked
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Verify patient exists
        patient = db.patients.find_one({"id": payload.patient_id})
        if not patient:
            logger.warning(f"Patient not found for KYC: {payload.patient_id}")
            raise PatientNotFoundError()
        
        # Hash and check for duplicate government ID
        govt_id_hash = hash_government_id(payload.govt_id)
        existing = db.patients.find_one({
            "govt_id_hash": govt_id_hash,
            "id": {"$ne": payload.patient_id}
        })
        if existing:
            logger.warning(
                f"Duplicate government ID attempt for patient {payload.patient_id}, "
                f"already linked to patient {existing['id']}"
            )
            raise DuplicateGovernmentIDError()
        
        # Update patient with KYC info
        try:
            db.patients.update_one(
                {"id": payload.patient_id},
                {
                    "$set": {
                        "name": payload.name,
                        "age": payload.age,
                        "gender": payload.gender,
                        "govt_id_hash": govt_id_hash,
                        "kyc_verified": True,
                    }
                },
            )
            logger.info(f"KYC completed for patient {payload.patient_id}")
        except Exception as e:
            logger.error(f"Failed to update patient {payload.patient_id}: {e}")
            raise DatabaseOperationError(
                operation="update_patient_kyc",
                original_error=e,
            )
        
        # Fetch updated patient
        updated = db.patients.find_one({"id": payload.patient_id})
        if not updated:
            raise PatientNotFoundError()
        
        updated.pop("_id", None)
        return PatientOut.model_validate(updated)
        
    except (PatientNotFoundError, DuplicateGovernmentIDError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"KYC completion failed: {e}")
        raise DatabaseOperationError(
            operation="complete_kyc",
            original_error=e,
        )
