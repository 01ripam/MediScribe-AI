import '../models/appointment.dart';
import 'api_client.dart';

class AppointmentService {
  final ApiClient _api;

  AppointmentService(this._api);

  Future<Appointment> create({required int patientId, required int doctorId, required String slot}) async {
    final json = await _api.postJson('/appointments', {
      'patient_id': patientId,
      'doctor_id': doctorId,
      'slot': slot,
    });
    return Appointment.fromJson(json);
  }

  Future<List<Appointment>> fetchByPatient(int patientId) async {
    final json = await _api.getList('/appointments', query: {'patient_id': '$patientId'});
    return json.map((dynamic e) => Appointment.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Appointment> patch(int appointmentId, String action) async {
    final json = await _api.patchJson('/appointments/$appointmentId', {'action': action});
    return Appointment.fromJson(json);
  }
}
