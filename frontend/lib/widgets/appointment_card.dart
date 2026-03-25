import 'package:flutter/material.dart';

import '../models/appointment.dart';

class AppointmentCard extends StatelessWidget {
  const AppointmentCard({
    super.key,
    required this.appointment,
    required this.onApprove,
    required this.onPay,
    required this.onCancel,
  });

  final Appointment appointment;
  final VoidCallback onApprove;
  final VoidCallback onPay;
  final VoidCallback onCancel;

  Color _statusColor(AppointmentStatus status) {
    switch (status) {
      case AppointmentStatus.requested:
        return Colors.orange;
      case AppointmentStatus.approved:
        return Colors.blue;
      case AppointmentStatus.confirmed:
        return Colors.green;
      case AppointmentStatus.cancelled:
        return Colors.red;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text('Appointment #${appointment.id}', style: const TextStyle(fontWeight: FontWeight.w700)),
                Chip(
                  backgroundColor: _statusColor(appointment.status).withAlpha(40),
                  label: Text(appointment.status.name.toUpperCase()),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text('Slot: ${appointment.slot}'),
            Text('Payment: ${appointment.paymentStatus.name.toUpperCase()}'),
            const SizedBox(height: 10),
            Row(
              children: <Widget>[
                if (appointment.status == AppointmentStatus.requested)
                  OutlinedButton(onPressed: onApprove, child: const Text('Simulate Approve')),
                if (appointment.status == AppointmentStatus.requested)
                  const SizedBox(width: 8),
                if (appointment.status == AppointmentStatus.approved)
                  FilledButton(onPressed: onPay, child: const Text('Pay & Confirm')),
                if (appointment.status != AppointmentStatus.confirmed && appointment.status != AppointmentStatus.cancelled)
                  TextButton(onPressed: onCancel, child: const Text('Cancel')),
              ],
            )
          ],
        ),
      ),
    );
  }
}
