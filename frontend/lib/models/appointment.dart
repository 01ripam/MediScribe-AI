enum AppointmentStatus { requested, approved, confirmed, cancelled }

enum PaymentStatus { pending, success, failed }

AppointmentStatus parseAppointmentStatus(String value) {
  switch (value) {
    case 'REQUESTED':
      return AppointmentStatus.requested;
    case 'APPROVED':
      return AppointmentStatus.approved;
    case 'CONFIRMED':
      return AppointmentStatus.confirmed;
    case 'CANCELLED':
      return AppointmentStatus.cancelled;
    default:
      return AppointmentStatus.requested;
  }
}

PaymentStatus parsePaymentStatus(String value) {
  switch (value) {
    case 'SUCCESS':
      return PaymentStatus.success;
    case 'FAILED':
      return PaymentStatus.failed;
    default:
      return PaymentStatus.pending;
  }
}

class Appointment {
  final int id;
  final int patientId;
  final int doctorId;
  final String slot;
  final AppointmentStatus status;
  final PaymentStatus paymentStatus;
  final String? paymentReference;
  final String? razorpayOrderId;
  final String patientStatus;

  const Appointment({
    required this.id,
    required this.patientId,
    required this.doctorId,
    required this.slot,
    required this.status,
    required this.paymentStatus,
    required this.paymentReference,
    this.razorpayOrderId,
    required this.patientStatus,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) {
    return Appointment(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      doctorId: json['doctor_id'] as int,
      slot: json['slot'] as String,
      status: parseAppointmentStatus(json['status'] as String),
      paymentStatus: parsePaymentStatus(json['payment_status'] as String),
      paymentReference: json['payment_reference'] as String?,
      razorpayOrderId: json['razorpay_order_id'] as String?,
      patientStatus: json['patient_status'] as String? ?? 'PENDING',
    );
  }
}
