import hashlib
import hmac
import json
import logging
import os
from typing import Optional
from uuid import uuid4

import razorpay

from ..exceptions import (
    RazorpayOrderCreationError,
    PaymentVerificationError,
    PaymentSignatureError,
    PaymentCaptureError,
)

logger = logging.getLogger(__name__)

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None
    logger.warning("Razorpay credentials not configured. Payments will use simulation mode.")


def create_razorpay_order(
    appointment_id: int,
    amount: float,
    patient_id: int,
    patient_email: str,
    patient_phone: str,
    doctor_name: str,
    description: str = "Medical Appointment",
) -> dict:
    """
    Create a Razorpay order for appointment payment.
    
    Args:
        appointment_id: Appointment ID
        amount: Amount in rupees (will be converted to paise)
        patient_id: Patient ID
        patient_email: Patient email
        patient_phone: Patient phone
        doctor_name: Doctor name for description
        description: Payment description
        
    Returns:
        Dictionary with order_id and order details
        
    Raises:
        RazorpayOrderCreationError: If order creation fails
    """
    if not razorpay_client:
        # Fallback to simulation when credentials not configured
        return _simulate_razorpay_order(appointment_id, amount, doctor_name)
    
    try:
        amount_paise = int(amount * 100)  # Convert to paise
        
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"appt_{appointment_id}",
            "notes": {
                "appointment_id": str(appointment_id),
                "patient_id": str(patient_id),
                "doctor_name": doctor_name,
            },
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        logger.info(f"Razorpay order created: {order['id']} for appointment {appointment_id}")
        
        return {
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "receipt": order["receipt"],
            "key_id": RAZORPAY_KEY_ID,
            "customer_email": patient_email,
            "customer_phone": patient_phone,
            "description": f"{description} - Dr. {doctor_name}",
        }
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay API error for appointment {appointment_id}: {str(e)}")
        raise RazorpayOrderCreationError(
            appointment_id=appointment_id,
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Failed to create Razorpay order for appointment {appointment_id}: {str(e)}")
        raise RazorpayOrderCreationError(
            appointment_id=appointment_id,
            original_error=e,
        )


def verify_razorpay_payment(
    razorpay_payment_id: str,
    razorpay_order_id: str,
    razorpay_signature: str,
) -> tuple[bool, Optional[str]]:
    """
    Verify Razorpay payment signature.
    
    Args:
        razorpay_payment_id: Payment ID from Razorpay
        razorpay_order_id: Order ID from Razorpay
        razorpay_signature: Signature for verification
        
    Returns:
        Tuple of (success, error_message)
        
    Raises:
        PaymentVerificationError: If verification fails due to unexpected error
    """
    if not razorpay_client:
        # Fallback to simulation when credentials not configured
        return True, None
    
    try:
        # Verify signature using HMAC-SHA256
        expected_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, razorpay_signature):
            logger.warning(
                f"Invalid signature for payment {razorpay_payment_id}",
                extra={"order_id": razorpay_order_id},
            )
            raise PaymentSignatureError()
        
        # Fetch payment details to verify captured status
        payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        payment_status = payment.get("status", "unknown")
        if payment_status != "captured":
            logger.warning(
                f"Payment {razorpay_payment_id} in {payment_status} status, expected: captured",
                extra={"payment_id": razorpay_payment_id, "status": payment_status},
            )
            raise PaymentVerificationError(
                reason=f"Payment is {payment_status}, expected: captured",
                payment_id=razorpay_payment_id,
            )
        
        logger.info(
            f"Payment {razorpay_payment_id} verified successfully",
            extra={"order_id": razorpay_order_id},
        )
        return True, None
        
    except (PaymentSignatureError, PaymentVerificationError):
        # Re-raise custom exceptions
        raise
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay API error during verification: {str(e)}")
        raise PaymentVerificationError(
            reason="Razorpay API error",
            payment_id=razorpay_payment_id,
        )
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise PaymentVerificationError(
            reason=str(e),
            payment_id=razorpay_payment_id,
        )


def capture_razorpay_payment(razorpay_payment_id: str, amount: float) -> tuple[bool, Optional[str]]:
    """
    Capture a Razorpay payment (for authorized payments).
    
    Args:
        razorpay_payment_id: Payment ID
        amount: Amount in rupees
        
    Returns:
        Tuple of (success, error_message)
        
    Raises:
        PaymentCaptureError: If capture fails
    """
    if not razorpay_client:
        return True, None
    
    try:
        amount_paise = int(amount * 100)
        payment = razorpay_client.payment.capture(razorpay_payment_id, amount_paise)
        
        logger.info(f"Payment {razorpay_payment_id} captured successfully")
        return True, None
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay API error while capturing payment: {str(e)}")
        raise PaymentCaptureError(
            payment_id=razorpay_payment_id,
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Payment capture failed: {str(e)}")
        raise PaymentCaptureError(
            payment_id=razorpay_payment_id,
            original_error=e,
        )


def validate_webhook_signature(body: str, signature: str) -> bool:
    """
    Validate Razorpay webhook signature.
    
    Args:
        body: Raw request body
        signature: X-Razorpay-Signature header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not RAZORPAY_KEY_SECRET:
        logger.warning("Razorpay key secret not configured, webhook validation skipped")
        return True
    
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def _simulate_razorpay_order(appointment_id: int, amount: float, doctor_name: str) -> dict:
    """
    Simulate Razorpay order creation for testing without credentials.
    
    Args:
        appointment_id: Appointment ID
        amount: Amount in rupees
        doctor_name: Doctor name
        
    Returns:
        Simulated order data
    """
    logger.warning(f"Using simulated order for appointment {appointment_id}")
    
    order_id = f"order_{uuid4().hex[:16]}"
    
    return {
        "success": True,
        "order_id": order_id,
        "amount": int(amount * 100),
        "currency": "INR",
        "receipt": f"appt_{appointment_id}",
        "key_id": "SIMULATION_KEY",
        "customer_email": "patient@example.com",
        "customer_phone": "9999999999",
        "description": f"Medical Appointment - Dr. {doctor_name}",
        "simulated": True,
    }

