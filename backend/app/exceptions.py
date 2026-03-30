"""
Custom exception classes for Patient Platform API.

This module provides a hierarchy of custom exceptions organized by domain.
All custom exceptions inherit from PatientPlatformException, enabling
consistent error handling and detailed error context.

Exception Hierarchy:
    PatientPlatformException (Base)
    ├── ConfigurationException
    ├── DatabaseException
    │   ├── DatabaseConnectionError
    │   ├── DatabaseOperationError
    │   └── ResourceNotFoundError
    ├── AuthenticationException
    │   ├── InvalidOTPError
    │   ├── PatientNotFoundError
    │   └── KYCNotCompletedError
    ├── PaymentException
    │   ├── RazorpayOrderCreationError
    │   ├── PaymentVerificationError
    │   └── PaymentSignatureError
    ├── AppointmentException
    │   ├── AppointmentNotFoundError
    │   ├── DoctorNotFoundError
    │   └── SlotConflictError
    ├── OTPException
    │   ├── OTPExpiredError
    │   └── InvalidOTPValueError
    └── ValidationException
        ├── InvalidInputError
        └── DuplicateResourceError
"""

from typing import Any, Optional
from http import HTTPStatus


class PatientPlatformException(Exception):
    """
    Base exception class for all custom exceptions in Patient Platform API.
    
    Provides consistent structure for error information including:
    - error_code: Unique identifier for the error
    - status_code: HTTP status code
    - message: User-friendly error message
    - details: Additional error context
    """

    error_code: str = "INTERNAL_ERROR"
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: User-friendly error message
            details: Additional context about the error
            original_error: The underlying exception that caused this error
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationException(PatientPlatformException):
    """Raised when required configuration is missing or invalid."""
    
    error_code = "CONFIGURATION_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class MissingEnvironmentVariableError(ConfigurationException):
    """Raised when a required environment variable is missing."""
    
    error_code = "MISSING_ENV_VARIABLE"
    
    def __init__(self, variable_name: str):
        super().__init__(
            message=f"Required environment variable '{variable_name}' is not set",
            details={"variable_name": variable_name},
        )


class InvalidConfigurationError(ConfigurationException):
    """Raised when configuration values are invalid."""
    
    error_code = "INVALID_CONFIGURATION"


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseException(PatientPlatformException):
    """Base exception for database-related errors."""
    
    error_code = "DATABASE_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class DatabaseConnectionError(DatabaseException):
    """Raised when unable to connect to the database."""
    
    error_code = "DATABASE_CONNECTION_ERROR"
    
    def __init__(self, connection_string: str, original_error: Optional[Exception] = None):
        super().__init__(
            message="Failed to connect to database. Check your database credentials and network.",
            details={"connection_attempt": "***hidden***"},
            original_error=original_error,
        )


class DatabaseOperationError(DatabaseException):
    """Raised when a database operation fails."""
    
    error_code = "DATABASE_OPERATION_ERROR"
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"Database {operation} operation failed",
            details={"operation": operation},
            original_error=original_error,
        )


class ResourceNotFoundError(DatabaseException):
    """Raised when a requested resource is not found in the database."""
    
    error_code = "RESOURCE_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        
        id_text = f" with ID {resource_id}" if resource_id else ""
        super().__init__(
            message=f"{resource_type}{id_text} not found",
            details=details,
        )


# ============================================================================
# Authentication Exceptions
# ============================================================================

class AuthenticationException(PatientPlatformException):
    """Base exception for authentication-related errors."""
    
    error_code = "AUTHENTICATION_ERROR"
    status_code = HTTPStatus.UNAUTHORIZED


class InvalidOTPError(AuthenticationException):
    """Raised when OTP validation fails."""
    
    error_code = "INVALID_OTP"
    status_code = HTTPStatus.BAD_REQUEST
    
    def __init__(self, reason: str = "Invalid or expired OTP"):
        super().__init__(
            message=reason,
            details={"error_type": "otp_validation"},
        )


class PatientNotFoundError(AuthenticationException):
    """Raised when patient is not found during authentication."""
    
    error_code = "PATIENT_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    
    def __init__(self, phone: Optional[str] = None):
        details = {}
        if phone:
            details["phone"] = f"{phone[:3]}****{phone[-2:]}" if len(phone) > 5 else "***"
        
        super().__init__(
            message="Patient account not found",
            details=details,
        )


class KYCNotCompletedError(AuthenticationException):
    """Raised when user tries to perform action requiring completed KYC."""
    
    error_code = "KYC_NOT_COMPLETED"
    status_code = HTTPStatus.FORBIDDEN
    
    def __init__(self, required_for: str = "this operation"):
        super().__init__(
            message=f"Complete KYC before {required_for}",
            details={"required_for": required_for},
        )


class DuplicateGovernmentIDError(AuthenticationException):
    """Raised when government ID is already linked to another account."""
    
    error_code = "DUPLICATE_GOVT_ID"
    status_code = HTTPStatus.CONFLICT
    
    def __init__(self):
        super().__init__(
            message="This government ID is already linked to another account",
            details={"error_type": "duplicate_resource"},
        )


# ============================================================================
# Payment Exceptions
# ============================================================================

class PaymentException(PatientPlatformException):
    """Base exception for payment-related errors."""
    
    error_code = "PAYMENT_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class RazorpayOrderCreationError(PaymentException):
    """Raised when Razorpay order creation fails."""
    
    error_code = "RAZORPAY_ORDER_CREATION_ERROR"
    
    def __init__(self, appointment_id: int, original_error: Optional[Exception] = None):
        super().__init__(
            message="Failed to create payment order with Razorpay",
            details={"appointment_id": appointment_id},
            original_error=original_error,
        )


class PaymentVerificationError(PaymentException):
    """Raised when payment verification fails."""
    
    error_code = "PAYMENT_VERIFICATION_ERROR"
    status_code = HTTPStatus.BAD_REQUEST
    
    def __init__(self, reason: str, payment_id: Optional[str] = None):
        details = {}
        if payment_id:
            details["payment_id"] = payment_id[-8:] if len(payment_id) > 8 else "***"
        
        super().__init__(
            message=f"Payment verification failed: {reason}",
            details=details,
        )


class PaymentSignatureError(PaymentException):
    """Raised when payment signature verification fails."""
    
    error_code = "PAYMENT_SIGNATURE_ERROR"
    status_code = HTTPStatus.UNAUTHORIZED
    
    def __init__(self):
        super().__init__(
            message="Invalid payment signature. Payment cannot be verified.",
            details={"error_type": "signature_verification"},
        )


class PaymentCaptureError(PaymentException):
    """Raised when payment capture fails."""
    
    error_code = "PAYMENT_CAPTURE_ERROR"
    
    def __init__(self, payment_id: str, original_error: Optional[Exception] = None):
        super().__init__(
            message="Failed to capture payment",
            details={"payment_id": payment_id[-8:]},
            original_error=original_error,
        )


# ============================================================================
# Appointment Exceptions
# ============================================================================

class AppointmentException(PatientPlatformException):
    """Base exception for appointment-related errors."""
    
    error_code = "APPOINTMENT_ERROR"
    status_code = HTTPStatus.BAD_REQUEST


class AppointmentNotFoundError(AppointmentException):
    """Raised when appointment is not found."""
    
    error_code = "APPOINTMENT_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    
    def __init__(self, appointment_id: int):
        super().__init__(
            message=f"Appointment {appointment_id} not found",
            details={"appointment_id": appointment_id},
        )


class DoctorNotFoundError(AppointmentException):
    """Raised when doctor is not found."""
    
    error_code = "DOCTOR_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    
    def __init__(self, doctor_id: int):
        super().__init__(
            message=f"Doctor {doctor_id} not found",
            details={"doctor_id": doctor_id},
        )


class SlotConflictError(AppointmentException):
    """Raised when appointment slot is already booked."""
    
    error_code = "SLOT_CONFLICT"
    status_code = HTTPStatus.CONFLICT
    
    def __init__(self, doctor_id: int, slot: str):
        super().__init__(
            message=f"Doctor is not available for slot {slot}",
            details={"doctor_id": doctor_id, "slot": slot},
        )


class InvalidAppointmentStatusError(AppointmentException):
    """Raised when appointment is in invalid status for operation."""
    
    error_code = "INVALID_APPOINTMENT_STATUS"
    
    def __init__(self, current_status: str, needed_status: str):
        super().__init__(
            message=f"Appointment is in {current_status} status, required: {needed_status}",
            details={"current_status": current_status, "needed_status": needed_status},
        )


# ============================================================================
# OTP Exceptions
# ============================================================================

class OTPException(PatientPlatformException):
    """Base exception for OTP-related errors."""
    
    error_code = "OTP_ERROR"
    status_code = HTTPStatus.BAD_REQUEST


class OTPExpiredError(OTPException):
    """Raised when OTP has expired."""
    
    error_code = "OTP_EXPIRED"
    
    def __init__(self, phone: Optional[str] = None):
        details = {}
        if phone:
            details["phone"] = f"{phone[:3]}****{phone[-2:]}" if len(phone) > 5 else "***"
        
        super().__init__(
            message="OTP has expired. Request a new OTP.",
            details=details,
        )


class InvalidOTPValueError(OTPException):
    """Raised when OTP value is incorrect."""
    
    error_code = "INVALID_OTP_VALUE"
    
    def __init__(self):
        super().__init__(
            message="The OTP you entered is incorrect",
            details={"error_type": "otp_mismatch"},
        )


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationException(PatientPlatformException):
    """Base exception for validation errors."""
    
    error_code = "VALIDATION_ERROR"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class InvalidInputError(ValidationException):
    """Raised when input validation fails."""
    
    error_code = "INVALID_INPUT"
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Invalid {field}: {reason}",
            details={"field": field, "reason": reason},
        )


class DuplicateResourceError(ValidationException):
    """Raised when attempting to create a resource that already exists."""
    
    error_code = "DUPLICATE_RESOURCE"
    status_code = HTTPStatus.CONFLICT
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with {identifier} already exists",
            details={"resource_type": resource_type, "identifier": identifier},
        )
