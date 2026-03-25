import '../models/patient.dart';
import 'api_client.dart';

class AuthService {
  final ApiClient _api;

  AuthService(this._api);

  Future<String> login(String phone) async {
    final json = await _api.postJson('/auth/login', {'phone': phone});
    return json['message'] as String;
  }

  Future<Patient> verifyOtp({required String phone, required String otp}) async {
    final json = await _api.postJson('/auth/verify-otp', {'phone': phone, 'otp': otp});
    return Patient.fromJson(json['patient'] as Map<String, dynamic>);
  }

  Future<Patient> completeKyc({
    required int patientId,
    required String name,
    required int age,
    required String gender,
    required String govtId,
    required String govtIdType,
  }) async {
    final json = await _api.postJson('/auth/kyc', {
      'patient_id': patientId,
      'name': name,
      'age': age,
      'gender': gender,
      'govt_id': govtId,
      'govt_id_type': govtIdType,
    });
    return Patient.fromJson(json);
  }
}
