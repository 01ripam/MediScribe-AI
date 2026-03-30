import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/doctor.dart';
import '../state/appointment_controller.dart';
import '../state/app_providers.dart';

class DoctorProfileScreen extends ConsumerStatefulWidget {
  const DoctorProfileScreen({super.key, required this.doctorId});

  final int doctorId;

  @override
  ConsumerState<DoctorProfileScreen> createState() => _DoctorProfileScreenState();
}

class _DoctorProfileScreenState extends ConsumerState<DoctorProfileScreen> {
  String? _selectedSlot;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Doctor>(
      future: ref.read(doctorServiceProvider).fetchDoctorById(widget.doctorId),
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
          body: ListView(
            padding: const EdgeInsets.all(16),
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
                        selected: _selectedSlot == slot,
                        onSelected: (bool selected) async {
                          if (!selected) {
                            setState(() => _selectedSlot = null);
                            return;
                          }

                          setState(() => _selectedSlot = slot);
                          try {
                            await ref.read(appointmentControllerProvider.notifier).requestAppointment(
                                  doctorId: doctor.id,
                                  slot: slot,
                                );
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Appointment requested for $slot')),
                              );
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
                              );
                            }
                          }
                        },
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 14),
              const Text('Busy Slots', style: TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              if (doctor.busySlots.isEmpty)
                const Text('No busy slots right now')
              else
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: doctor.busySlots
                      .map(
                        (String slot) => Chip(
                          label: Text(slot),
                          avatar: const Icon(Icons.block, size: 18),
                        ),
                      )
                      .toList(),
                ),
            ],
          ),
        );
      },
    );
  }
}
