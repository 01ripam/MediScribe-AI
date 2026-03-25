from uuid import uuid4


def simulate_razorpay_payment(appointment_id: int) -> tuple[bool, str]:
    """Return success and fake payment reference.

    This deterministic strategy keeps local testing predictable.
    """
    reference = f"pay_{uuid4().hex[:10]}"
    success = True if appointment_id >= 0 else False
    return success, reference
