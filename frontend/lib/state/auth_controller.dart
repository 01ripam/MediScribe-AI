import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/patient.dart';
import 'app_providers.dart';

class AuthState {
  final bool loading;
  final String? message;
  final String? error;
  final Patient? patient;

  const AuthState({this.loading = false, this.message, this.error, this.patient});

  AuthState copyWith({bool? loading, String? message, String? error, Patient? patient}) {
    return AuthState(
      loading: loading ?? this.loading,
      message: message,
      error: error,
      patient: patient ?? this.patient,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this.ref) : super(const AuthState());

  final Ref ref;

  Future<void> login(String phone) async {
    state = state.copyWith(loading: true, error: null, message: null);
    try {
      final message = await ref.read(authServiceProvider).login(phone);
      state = state.copyWith(loading: false, message: message, error: null);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<void> verifyOtp({required String phone, required String otp}) async {
    state = state.copyWith(loading: true, error: null);
    try {
      final patient = await ref.read(authServiceProvider).verifyOtp(phone: phone, otp: otp);
      state = state.copyWith(loading: false, patient: patient, error: null);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<void> completeKyc({
    required String name,
    required int age,
    required String gender,
    required String govtId,
    required String govtIdType,
  }) async {
    final currentPatient = state.patient;
    if (currentPatient == null) {
      state = state.copyWith(error: 'Login first');
      return;
    }
    state = state.copyWith(loading: true, error: null);
    try {
      final updatedPatient = await ref.read(authServiceProvider).completeKyc(
        patientId: currentPatient.id,
        name: name,
        age: age,
        gender: gender,
        govtId: govtId,
        govtIdType: govtIdType,
      );
      state = state.copyWith(loading: false, patient: updatedPatient);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  void signOut() {
    state = const AuthState();
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref);
});
