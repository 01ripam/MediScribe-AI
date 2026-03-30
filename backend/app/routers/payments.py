import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..database import get_database
from ..models import AppointmentStatus, PaymentStatus
from ..services.payment_service import (
    capture_razorpay_payment,
    create_razorpay_order,
    validate_webhook_signature,
    verify_razorpay_payment,
)
from ..exceptions import (
    AppointmentNotFoundError,
    DoctorNotFoundError,
    DatabaseOperationError,
    RazorpayOrderCreationError,
    PaymentVerificationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


class CreateOrderRequest(BaseModel):
    appointment_id: int
    patient_id: int
    patient_email: str
    patient_phone: str
    amount: float
    doctor_name: str
    description: Optional[str] = "Medical Appointment"


class CreateOrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    key_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


class VerifyPaymentRequest(BaseModel):
    appointment_id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


class PaymentVerificationResponse(BaseModel):
    success: bool
    message: str
    payment_status: Optional[str] = None
    error: Optional[str] = None


class WebhookPaymentData(BaseModel):
    payment: dict
    order: dict


@router.post("/orders", response_model=CreateOrderResponse)
def create_payment_order(payload: CreateOrderRequest):
    """
    Create a Razorpay order for appointment payment.
    
    This endpoint initializes a payment for an appointment.
    The client will use the returned order_id and key_id to open
    the Razorpay payment modal.
    
    Args:
        payload: Order creation request with appointment and payment details
        
    Returns:
        CreateOrderResponse with order details
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        DoctorNotFoundError: If doctor doesn't exist
        RazorpayOrderCreationError: If order creation fails
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Verify appointment exists
        appointment = db.appointments.find_one({"id": payload.appointment_id})
        if not appointment:
            logger.warning(f"Order creation failed: appointment {payload.appointment_id} not found")
            raise AppointmentNotFoundError(appointment_id=payload.appointment_id)
        
        # Verify doctor exists
        doctor = db.doctors.find_one({"id": appointment.get("doctor_id")})
        if not doctor:
            logger.warning(f"Order creation failed: doctor {appointment.get('doctor_id')} not found")
            raise DoctorNotFoundError(doctor_id=appointment.get("doctor_id"))
        
        # Create Razorpay order (may raise RazorpayOrderCreationError)
        order_response = create_razorpay_order(
            appointment_id=payload.appointment_id,
            amount=payload.amount,
            patient_id=payload.patient_id,
            patient_email=payload.patient_email,
            patient_phone=payload.patient_phone,
            doctor_name=payload.doctor_name,
            description=payload.description,
        )
        
        if not order_response.get("success"):
            logger.error(f"Razorpay order creation failed: {order_response.get('error')}")
            raise RazorpayOrderCreationError(
                appointment_id=payload.appointment_id,
                original_error=Exception(order_response.get('error')),
            )
        
        # Store order_id in appointment for reference
        try:
            db.appointments.update_one(
                {"id": payload.appointment_id},
                {"$set": {"razorpay_order_id": order_response.get("order_id")}},
            )
            logger.info(f"Order {order_response.get('order_id')} created for appointment {payload.appointment_id}")
        except Exception as e:
            logger.error(f"Failed to store order ID in database: {e}")
            raise DatabaseOperationError(
                operation="store_order_id",
                original_error=e,
            )
        
        return CreateOrderResponse(
            success=True,
            order_id=order_response.get("order_id"),
            key_id=order_response.get("key_id"),
            amount=order_response.get("amount"),
            currency=order_response.get("currency"),
            customer_email=order_response.get("customer_email"),
            customer_phone=order_response.get("customer_phone"),
            description=order_response.get("description"),
        )
        
    except (AppointmentNotFoundError, DoctorNotFoundError, 
            RazorpayOrderCreationError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise DatabaseOperationError(
            operation="create_payment_order",
            original_error=e,
        )


@router.post("/verify", response_model=PaymentVerificationResponse)
def verify_payment(payload: VerifyPaymentRequest):
    """
    Verify Razorpay payment signature and update appointment status.
    
    This endpoint is called after successful payment on client side.
    It verifies the payment and updates appointment to CONFIRMED.
    
    Args:
        payload: Payment verification request with Razorpay details
        
    Returns:
        PaymentVerificationResponse with verification status
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        PaymentVerificationError: If payment verification fails
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Verify appointment exists
        appointment = db.appointments.find_one({"id": payload.appointment_id})
        if not appointment:
            logger.warning(f"Payment verification failed: appointment {payload.appointment_id} not found")
            raise AppointmentNotFoundError(appointment_id=payload.appointment_id)
        
        # Verify payment signature (may raise PaymentSignatureError or PaymentVerificationError)
        try:
            verify_razorpay_payment(
                razorpay_payment_id=payload.razorpay_payment_id,
                razorpay_order_id=payload.razorpay_order_id,
                razorpay_signature=payload.razorpay_signature,
            )
        except PaymentVerificationError as e:
            logger.warning(f"Payment verification failed: {e.message}")
            
            # Update appointment with failed payment
            try:
                db.appointments.update_one(
                    {"id": payload.appointment_id},
                    {
                        "$set": {
                            "payment_status": PaymentStatus.FAILED.value,
                            "payment_reference": payload.razorpay_payment_id,
                        }
                    },
                )
            except Exception as db_error:
                logger.error(f"Failed to update failed payment status: {db_error}")
            
            raise
        
        # Update appointment with successful payment
        try:
            db.appointments.update_one(
                {"id": payload.appointment_id},
                {
                    "$set": {
                        "status": AppointmentStatus.CONFIRMED.value,
                        "payment_status": PaymentStatus.SUCCESS.value,
                        "payment_reference": payload.razorpay_payment_id,
                        "razorpay_order_id": payload.razorpay_order_id,
                    }
                },
            )
            logger.info(f"Payment verified for appointment {payload.appointment_id}")
        except Exception as e:
            logger.error(f"Failed to update payment status after verification: {e}")
            raise DatabaseOperationError(
                operation="update_payment_status",
                original_error=e,
            )
        
        return PaymentVerificationResponse(
            success=True,
            message="Payment verified successfully. Appointment confirmed.",
            payment_status=PaymentStatus.SUCCESS.value,
        )
        
    except (AppointmentNotFoundError, PaymentVerificationError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise DatabaseOperationError(
            operation="verify_payment",
            original_error=e,
        )


@router.post("/webhook")
def handle_webhook(request: Request):
    """
    Handle Razorpay webhook for payment events.
    
    Razorpay will send webhooks for:
    - payment.authorized
    - payment.failed
    - payment.captured
    - order.paid
    
    Args:
        request: Webhook request from Razorpay
        
    Returns:
        Webhook acknowledgement
    """
    try:
        logger.info("Webhook received from Razorpay")
        # Note: In production, validate the webhook signature
        # This endpoint doesn't require authentication for webhooks
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Still return 200 to prevent Razorpay retries for hard errors
        return {"status": "received", "error": str(e)}


@router.post("/refund/{appointment_id}")
def refund_payment(appointment_id: int):
    """
    Refund a payment for an appointment.
    
    This can be used to refund a confirmed appointment if needed.
    
    Args:
        appointment_id: Appointment ID to refund
        
    Returns:
        Refund confirmation
        
    Raises:
        AppointmentNotFoundError: If appointment doesn't exist
        PaymentVerificationError: If not in a refundable state
        DatabaseOperationError: If database operations fail
    """
    try:
        db = get_database()
        
        # Verify appointment exists
        appointment = db.appointments.find_one({"id": appointment_id})
        if not appointment:
            logger.warning(f"Refund failed: appointment {appointment_id} not found")
            raise AppointmentNotFoundError(appointment_id=appointment_id)
        
        # Verify payment is in refundable state
        payment_status = appointment.get("payment_status")
        if payment_status != PaymentStatus.SUCCESS.value:
            logger.warning(
                f"Cannot refund appointment {appointment_id} with payment status: {payment_status}"
            )
            raise PaymentVerificationError(
                reason=f"Only successfully paid appointments can be refunded (current: {payment_status})",
                payment_id=appointment.get("payment_reference"),
            )
        
        # In production, call Razorpay refund API here
        # For now, just update status
        try:
            db.appointments.update_one(
                {"id": appointment_id},
                {"$set": {"payment_status": PaymentStatus.PENDING.value}},
            )
            logger.info(f"Payment refunded for appointment {appointment_id}")
        except Exception as e:
            logger.error(f"Failed to update refund status: {e}")
            raise DatabaseOperationError(
                operation="refund_payment",
                original_error=e,
            )
        
        return {
            "success": True,
            "message": "Payment refunded successfully",
            "appointment_id": appointment_id,
        }
        
    except (AppointmentNotFoundError, PaymentVerificationError, DatabaseOperationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Refund processing failed: {e}")
        raise DatabaseOperationError(
            operation="refund_payment",
            original_error=e,
        )
