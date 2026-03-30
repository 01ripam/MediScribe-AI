import 'package:razorpay_flutter/razorpay_flutter.dart';
import 'api_client.dart';

class PaymentOrder {
  final bool success;
  final String? orderId;
  final String? keyId;
  final int? amount;
  final String? currency;
  final String? customerEmail;
  final String? customerPhone;
  final String? description;
  final String? error;

  PaymentOrder({
    required this.success,
    this.orderId,
    this.keyId,
    this.amount,
    this.currency,
    this.customerEmail,
    this.customerPhone,
    this.description,
    this.error,
  });

  factory PaymentOrder.fromJson(Map<String, dynamic> json) {
    return PaymentOrder(
      success: json['success'] as bool,
      orderId: json['order_id'] as String?,
      keyId: json['key_id'] as String?,
      amount: json['amount'] as int?,
      currency: json['currency'] as String?,
      customerEmail: json['customer_email'] as String?,
      customerPhone: json['customer_phone'] as String?,
      description: json['description'] as String?,
      error: json['error'] as String?,
    );
  }
}

class PaymentVerificationResult {
  final bool success;
  final String message;
  final String? paymentStatus;
  final String? error;

  PaymentVerificationResult({
    required this.success,
    required this.message,
    this.paymentStatus,
    this.error,
  });

  factory PaymentVerificationResult.fromJson(Map<String, dynamic> json) {
    return PaymentVerificationResult(
      success: json['success'] as bool,
      message: json['message'] as String,
      paymentStatus: json['payment_status'] as String?,
      error: json['error'] as String?,
    );
  }
}

typedef PaymentSuccessCallback = void Function(PaymentSuccessResponse);
typedef PaymentErrorCallback = void Function(PaymentFailureResponse);
typedef PaymentExternalWalletCallback = void Function(dynamic);

class PaymentService {
  final ApiClient _api;
  final Razorpay _razorpay = Razorpay();
  late PaymentSuccessCallback _onSuccess;
  late PaymentErrorCallback _onError;
  late PaymentExternalWalletCallback _onWallet;

  PaymentService(this._api) {
    _initializeCallbacks();
  }

  void _initializeCallbacks() {
    _razorpay.on(Razorpay.EVENT_PAYMENT_SUCCESS, _handlePaymentSuccess);
    _razorpay.on(Razorpay.EVENT_PAYMENT_ERROR, _handlePaymentError);
    _razorpay.on(Razorpay.EVENT_EXTERNAL_WALLET, _handleExternalWallet);
  }

  /// Create a payment order for an appointment
  Future<PaymentOrder> createPaymentOrder({
    required int appointmentId,
    required int patientId,
    required String patientEmail,
    required String patientPhone,
    required double amount,
    required String doctorName,
    String description = 'Medical Appointment',
  }) async {
    try {
      final response = await _api.postJson('/payments/orders', {
        'appointment_id': appointmentId,
        'patient_id': patientId,
        'patient_email': patientEmail,
        'patient_phone': patientPhone,
        'amount': amount,
        'doctor_name': doctorName,
        'description': description,
      });

      if (response['success'] == true) {
        return PaymentOrder.fromJson(response);
      } else {
        return PaymentOrder.fromJson(response);
      }
    } catch (e) {
      return PaymentOrder(
        success: false,
        error: 'Failed to create payment order: ${e.toString()}',
      );
    }
  }

  /// Open Razorpay payment modal
  void openPaymentModal({
    required PaymentOrder order,
    required String userEmail,
    required String userPhone,
    required String userName,
    required PaymentSuccessCallback onSuccess,
    required PaymentErrorCallback onError,
    required PaymentExternalWalletCallback onWallet,
  }) {
    _onSuccess = onSuccess;
    _onError = onError;
    _onWallet = onWallet;

    final options = {
      'key': order.keyId,
      'amount': order.amount, // amount in smallest currency unit (paise)
      'name': 'Patient Platform',
      'description': order.description,
      'order_id': order.orderId,
      'currency': order.currency ?? 'INR',
      'prefill': {
        'contact': userPhone,
        'email': userEmail,
        'name': userName,
      },
      'theme': {
        'color': '#0066CC',
      },
    };

    try {
      _razorpay.open(options);
    } catch (e) {
      onError(
        PaymentFailureResponse(
          -1,
          'Error opening payment modal: ${e.toString()}',
          <String, dynamic>{},
        ),
      );
    }
  }

  /// Verify payment after successful payment on client
  Future<PaymentVerificationResult> verifyPayment({
    required int appointmentId,
    required String paymentId,
    required String orderId,
    required String signature,
  }) async {
    try {
      final response = await _api.postJson('/payments/verify', {
        'appointment_id': appointmentId,
        'razorpay_payment_id': paymentId,
        'razorpay_order_id': orderId,
        'razorpay_signature': signature,
      });

      return PaymentVerificationResult.fromJson(response);
    } catch (e) {
      return PaymentVerificationResult(
        success: false,
        message: 'Payment verification failed',
        error: e.toString(),
      );
    }
  }

  /// Refund a payment
  Future<bool> refundPayment(int appointmentId) async {
    try {
      final response = await _api.postJson('/payments/refund/$appointmentId', {});
      return response['success'] as bool;
    } catch (e) {
      return false;
    }
  }

  // Internal callback handlers
  void _handlePaymentSuccess(PaymentSuccessResponse response) {
    _onSuccess(response);
  }

  void _handlePaymentError(PaymentFailureResponse response) {
    _onError(response);
  }

  void _handleExternalWallet(dynamic response) {
    _onWallet(response);
  }

  /// Clean up resources
  void dispose() {
    _razorpay.clear();
  }
}
