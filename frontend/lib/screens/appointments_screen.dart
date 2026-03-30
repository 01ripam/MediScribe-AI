import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import '../models/appointment.dart';
import '../state/appointment_controller.dart';
import '../state/app_providers.dart';
import '../state/auth_controller.dart';
import '../widgets/appointment_card.dart';
import '../widgets/appointment_payment_dialog.dart';

class AppointmentsScreen extends ConsumerStatefulWidget {
  const AppointmentsScreen({super.key});

  @override
  ConsumerState<AppointmentsScreen> createState() => _AppointmentsScreenState();
}

class _AppointmentsScreenState extends ConsumerState<AppointmentsScreen> {
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  @override
  void initState() {
    super.initState();
    _selectedDay = DateTime.now();
    Future<void>.microtask(() => ref.read(appointmentControllerProvider.notifier).refresh());
  }

  DateTime? _slotToDate(String slot) {
    try {
      final parsed = DateFormat('yyyy-MM-dd hh:mm a').parseStrict(slot);
      return DateTime(parsed.year, parsed.month, parsed.day);
    } catch (_) {
      return null;
    }
  }

  Future<void> _openPaymentDialog(Appointment appointment) async {
    final patient = ref.read(authControllerProvider).patient;
    if (patient == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please login first')),
        );
      }
      return;
    }

    final doctor = await ref.read(doctorServiceProvider).fetchDoctorById(appointment.doctorId);
    final paymentService = ref.read(paymentServiceProvider);

    if (!mounted) {
      return;
    }

    await showDialog<void>(
      context: context,
      builder: (BuildContext context) {
        return AppointmentPaymentDialog(
          appointment: appointment,
          doctor: doctor,
          patient: patient,
          paymentService: paymentService,
          onPaymentSuccess: () {
            ref.read(appointmentControllerProvider.notifier).refresh();
          },
          onPaymentError: (_) {},
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final appointmentsAsync = ref.watch(appointmentControllerProvider);
    return DefaultTabController(
      length: 4,
      child: SafeArea(
        child: Column(
          children: <Widget>[
            const TabBar(tabs: <Widget>[Tab(text: 'Upcoming'), Tab(text: 'Completed'), Tab(text: 'Cancelled'), Tab(text: 'Calendar')]),
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
                      _buildCalendar(items),
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
          onPay: () => _openPaymentDialog(item),
          onCancel: () => ref.read(appointmentControllerProvider.notifier).cancel(item.id),
        );
      },
    );
  }

  Widget _buildCalendar(List<Appointment> items) {
    final selectedDay = _selectedDay ?? DateTime.now();
    // Filter out cancelled appointments from calendar
    final activeItems = items.where((Appointment a) => a.status != AppointmentStatus.cancelled).toList();
    
    final selectedItems = activeItems.where((Appointment appointment) {
      final day = _slotToDate(appointment.slot);
      return day != null && isSameDay(day, selectedDay);
    }).toList();

    final eventsByDay = <String, int>{};
    for (final appointment in activeItems) {
      final day = _slotToDate(appointment.slot);
      if (day == null) {
        continue;
      }
      final key = DateFormat('yyyy-MM-dd').format(day);
      eventsByDay[key] = (eventsByDay[key] ?? 0) + 1;
    }

    return Column(
      children: <Widget>[
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: TableCalendar<int>(
            firstDay: DateTime.now().subtract(const Duration(days: 365)),
            lastDay: DateTime.now().add(const Duration(days: 365)),
            focusedDay: _focusedDay,
            selectedDayPredicate: (DateTime day) => isSameDay(_selectedDay, day),
            onDaySelected: (DateTime selected, DateTime focused) {
              setState(() {
                _selectedDay = selected;
                _focusedDay = focused;
              });
            },
            eventLoader: (DateTime day) {
              final key = DateFormat('yyyy-MM-dd').format(day);
              final count = eventsByDay[key] ?? 0;
              return count == 0 ? const <int>[] : List<int>.filled(count, 1);
            },
          ),
        ),
        const SizedBox(height: 8),
        Expanded(child: _buildList(selectedItems)),
      ],
    );
  }
}
