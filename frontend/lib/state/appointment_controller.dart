import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/appointment.dart';
import 'app_providers.dart';
import 'auth_controller.dart';

class AppointmentController extends StateNotifier<AsyncValue<List<Appointment>>> {
  AppointmentController(this.ref) : super(const AsyncValue.data(<Appointment>[]));

  final Ref ref;

  Future<void> refresh() async {
    final patientId = ref.read(authControllerProvider).patient?.id;
    if (patientId == null) {
      state = const AsyncValue.data(<Appointment>[]);
      return;
    }
    state = const AsyncValue.loading();
    try {
      final appointments = await ref.read(appointmentServiceProvider).fetchByPatient(patientId);
      state = AsyncValue.data(appointments);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> requestAppointment({required int doctorId, required String slot}) async {
    final patientId = ref.read(authControllerProvider).patient?.id;
    if (patientId == null) {
      throw StateError('Please login first to book an appointment');
    }
    await ref.read(appointmentServiceProvider).create(patientId: patientId, doctorId: doctorId, slot: slot);
    await refresh();
  }

  Future<void> payForAppointment(int appointmentId) async {
    await ref.read(appointmentServiceProvider).patch(appointmentId, 'pay');
    await refresh();
  }

  Future<void> approveForDemo(int appointmentId) async {
    await ref.read(appointmentServiceProvider).patch(appointmentId, 'approve');
    await refresh();
  }

  Future<void> cancel(int appointmentId) async {
    await ref.read(appointmentServiceProvider).patch(appointmentId, 'cancel');
    await refresh();
  }
}

final appointmentControllerProvider = StateNotifierProvider<AppointmentController, AsyncValue<List<Appointment>>>((ref) {
  return AppointmentController(ref);
});
