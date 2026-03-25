import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/appointment.dart';
import '../state/appointment_controller.dart';
import '../widgets/appointment_card.dart';

class AppointmentsScreen extends ConsumerStatefulWidget {
  const AppointmentsScreen({super.key});

  @override
  ConsumerState<AppointmentsScreen> createState() => _AppointmentsScreenState();
}

class _AppointmentsScreenState extends ConsumerState<AppointmentsScreen> {
  @override
  void initState() {
    super.initState();
    Future<void>.microtask(() => ref.read(appointmentControllerProvider.notifier).refresh());
  }

  @override
  Widget build(BuildContext context) {
    final appointmentsAsync = ref.watch(appointmentControllerProvider);
    return DefaultTabController(
      length: 3,
      child: SafeArea(
        child: Column(
          children: <Widget>[
            const TabBar(tabs: <Widget>[Tab(text: 'Upcoming'), Tab(text: 'Completed'), Tab(text: 'Cancelled')]),
            Expanded(
              child: appointmentsAsync.when(
                data: (List<Appointment> items) {
                  final upcoming = items.where((Appointment a) => a.status == AppointmentStatus.requested || a.status == AppointmentStatus.approved).toList();
                  final completed = items.where((Appointment a) => a.status == AppointmentStatus.confirmed).toList();
                  final cancelled = items.where((Appointment a) => a.status == AppointmentStatus.cancelled).toList();

                  return TabBarView(
                    children: <Widget>[
                      _buildList(upcoming),
                      _buildList(completed),
                      _buildList(cancelled),
                    ],
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (Object e, StackTrace _) => Center(child: Text(e.toString())),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildList(List<Appointment> items) {
    if (items.isEmpty) {
      return const Center(child: Text('No appointments found'));
    }
    return ListView.builder(
      itemCount: items.length,
      padding: const EdgeInsets.all(16),
      itemBuilder: (BuildContext context, int index) {
        final item = items[index];
        return AppointmentCard(
          appointment: item,
          onApprove: () => ref.read(appointmentControllerProvider.notifier).approveForDemo(item.id),
          onPay: () => ref.read(appointmentControllerProvider.notifier).payForAppointment(item.id),
          onCancel: () => ref.read(appointmentControllerProvider.notifier).cancel(item.id),
        );
      },
    );
  }
}
