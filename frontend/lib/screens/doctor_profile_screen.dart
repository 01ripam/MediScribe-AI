import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/doctor.dart';
import '../state/appointment_controller.dart';
import '../state/app_providers.dart';

class DoctorProfileScreen extends ConsumerWidget {
  const DoctorProfileScreen({super.key, required this.doctorId});

  final int doctorId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Doctor>(
      future: ref.read(doctorServiceProvider).fetchDoctorById(doctorId),
      builder: (BuildContext context, AsyncSnapshot<Doctor> snapshot) {
        if (!snapshot.hasData) {
          if (snapshot.hasError) {
            return Scaffold(appBar: AppBar(), body: Center(child: Text(snapshot.error.toString())));
          }
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }

        final doctor = snapshot.data!;
        return Scaffold(
          appBar: AppBar(title: const Text('Doctor Profile')),
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(doctor.name, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text('${doctor.specialization} • ${doctor.experience} years'),
                const SizedBox(height: 4),
                Text('Fees: ₹${doctor.fees.toStringAsFixed(0)} • Rating ${doctor.rating.toStringAsFixed(1)}'),
                const SizedBox(height: 10),
                Text(doctor.bio),
                const SizedBox(height: 14),
                const Text('Available Slots', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: doctor.availableSlots
                      .map(
                        (String slot) => ChoiceChip(
                          label: Text(slot),
                          selected: false,
                          onSelected: (_) async {
                            await ref.read(appointmentControllerProvider.notifier).requestAppointment(doctorId: doctor.id, slot: slot);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Appointment requested')));
                            }
                          },
                        ),
                      )
                      .toList(),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
