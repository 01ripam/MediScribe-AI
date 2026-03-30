import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/api_client.dart';
import '../services/appointment_service.dart';
import '../services/auth_service.dart';
import '../services/doctor_service.dart';
import '../services/pharmacy_service.dart';
import '../services/payment_service.dart';
import '../services/record_service.dart';

final localeProvider = StateProvider<Locale>((ref) => const Locale('en'));

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final authServiceProvider = Provider<AuthService>((ref) => AuthService(ref.read(apiClientProvider)));
final doctorServiceProvider = Provider<DoctorService>((ref) => DoctorService(ref.read(apiClientProvider)));
final appointmentServiceProvider = Provider<AppointmentService>((ref) => AppointmentService(ref.read(apiClientProvider)));
final paymentServiceProvider = Provider<PaymentService>((ref) => PaymentService(ref.read(apiClientProvider)));
final recordServiceProvider = Provider<RecordService>((ref) => RecordService(ref.read(apiClientProvider)));
final pharmacyServiceProvider = Provider<PharmacyService>((ref) => PharmacyService());
