import 'package:flutter/material.dart';
import 'package:razorpay_flutter/razorpay_flutter.dart';
import '../models/appointment.dart';
import '../models/doctor.dart';
import '../models/patient.dart';
import '../services/payment_service.dart';

enum InAppPaymentMethod { upi, card, netbanking, wallet }

class AppointmentPaymentDialog extends StatefulWidget {
  final Appointment appointment;
  final Doctor doctor;
  final Patient patient;
  final PaymentService paymentService;
  final VoidCallback onPaymentSuccess;
  final Function(String) onPaymentError;

  const AppointmentPaymentDialog({
    super.key,
    required this.appointment,
    required this.doctor,
    required this.patient,
    required this.paymentService,
    required this.onPaymentSuccess,
    required this.onPaymentError,
  });

  @override
  State<AppointmentPaymentDialog> createState() => _AppointmentPaymentDialogState();
}

class _AppointmentPaymentDialogState extends State<AppointmentPaymentDialog> {
  bool _isLoading = false;
  String? _errorMessage;
  InAppPaymentMethod? _selectedMethod;

  bool _isSimulationOrder(PaymentOrder order) {
    return order.keyId == 'SIMULATION_KEY' ||
        (order.orderId?.startsWith('order_') ?? false);
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Payment Required',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            _buildPaymentDetails(),
            const SizedBox(height: 24),
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
              const SizedBox(height: 16),
            ],
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: _isLoading ? null : () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLoading ? null : _processPayment,
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Continue to Pay'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPaymentDetails() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildDetailRow('Doctor', widget.doctor.name),
        _buildDetailRow('Appointment', widget.appointment.slot),
        _buildDetailRow('Fees', '₹${widget.doctor.fees.toStringAsFixed(2)}'),
        const Divider(height: 24),
        _buildDetailRow(
          'Amount',
          '₹${widget.doctor.fees.toStringAsFixed(2)}',
          isBold: true,
        ),
        const SizedBox(height: 12),
        const Text(
          'Select Payment Method',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ChoiceChip(
              label: const Text('UPI'),
              selected: _selectedMethod == InAppPaymentMethod.upi,
              onSelected: (_) => setState(() => _selectedMethod = InAppPaymentMethod.upi),
            ),
            ChoiceChip(
              label: const Text('Card'),
              selected: _selectedMethod == InAppPaymentMethod.card,
              onSelected: (_) => setState(() => _selectedMethod = InAppPaymentMethod.card),
            ),
            ChoiceChip(
              label: const Text('Netbanking'),
              selected: _selectedMethod == InAppPaymentMethod.netbanking,
              onSelected: (_) => setState(() => _selectedMethod = InAppPaymentMethod.netbanking),
            ),
            ChoiceChip(
              label: const Text('Wallet'),
              selected: _selectedMethod == InAppPaymentMethod.wallet,
              onSelected: (_) => setState(() => _selectedMethod = InAppPaymentMethod.wallet),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: TextStyle(
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _processPayment() async {
    if (_selectedMethod == null) {
      _setError('Please select a payment method first');
      return;
    }

    setState(() => _isLoading = true);
    _clearError();

    try {
      // Step 1: Create payment order
      final order = await widget.paymentService.createPaymentOrder(
        appointmentId: widget.appointment.id,
        patientId: widget.patient.id,
        patientEmail: 'patient${widget.patient.id}@example.com',
        patientPhone: widget.patient.phone,
        amount: widget.doctor.fees,
        doctorName: widget.doctor.name,
      );

      if (!order.success) {
        _setError(order.error ?? 'Failed to create payment order');
        return;
      }

      if (_isSimulationOrder(order)) {
        // In simulation mode, verify directly with backend instead of opening SDK checkout.
        final result = await widget.paymentService.verifyPayment(
          appointmentId: widget.appointment.id,
          paymentId: 'pay_sim_${widget.appointment.id}',
          orderId: order.orderId ?? 'order_sim_${widget.appointment.id}',
          signature: 'simulated_signature',
        );

        if (result.success) {
          if (mounted) {
            Navigator.pop(context);
            widget.onPaymentSuccess();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Simulation payment successful! Appointment confirmed.'),
                backgroundColor: Colors.green,
              ),
            );
          }
        } else {
          _setError(result.error ?? result.message);
        }
        return;
      }

      if (mounted) {
        // Step 2: Open Razorpay modal
        widget.paymentService.openPaymentModal(
          order: order,
          userEmail: 'patient${widget.patient.id}@example.com',
          userPhone: widget.patient.phone,
          userName: widget.patient.name ?? 'Patient',
          onSuccess: _onPaymentSuccess,
          onError: _onPaymentError,
          onWallet: _onExternalWallet,
        );
      }
    } catch (e) {
      _setError('Error: ${e.toString()}');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _onPaymentSuccess(PaymentSuccessResponse response) async {
    if (!mounted) return;

    // Step 3: Verify payment with backend
    setState(() => _isLoading = true);
    _clearError();

    try {
      final result = await widget.paymentService.verifyPayment(
        appointmentId: widget.appointment.id,
        paymentId: response.paymentId ?? '',
        orderId: response.orderId ?? '',
        signature: response.signature ?? '',
      );

      if (mounted) {
        if (result.success) {
          // Payment verified successfully
          Navigator.pop(context);
          widget.onPaymentSuccess();
          
          // Show success message
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Payment successful! Appointment confirmed.'),
              backgroundColor: Colors.green,
            ),
          );
        } else {
          _setError(result.error ?? result.message);
        }
      }
    } catch (e) {
      if (mounted) {
        _setError('Verification error: ${e.toString()}');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _onPaymentError(PaymentFailureResponse response) {
    if (!mounted) return;
    
    _setError(response.message ?? 'Payment failed');
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Payment failed: ${response.message}'),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _onExternalWallet(dynamic response) {
    final walletName = response?.walletName?.toString() ?? 'External Wallet';
    // User selected external wallet
    _setError('External wallet selected: $walletName. Please complete the payment in the wallet app.');
  }

  void _setError(String message) {
    setState(() => _errorMessage = message);
    widget.onPaymentError(message);
  }

  void _clearError() {
    setState(() => _errorMessage = null);
  }

  @override
  void dispose() {
    // Payment service callbacks will be handled automatically
    super.dispose();
  }
}

/// Example usage in an appointment list screen:
/// 
/// ```dart
/// showDialog(
///   context: context,
///   builder: (context) => AppointmentPaymentDialog(
///     appointment: appointment,
///     doctor: doctor,
///     patient: patient,
///     paymentService: paymentService,
///     onPaymentSuccess: () {
///       // Refresh appointment list or navigate
///       _refreshAppointments();
///     },
///     onPaymentError: (error) {
///       print('Payment error: $error');
///     },
///   ),
/// );
/// ```
