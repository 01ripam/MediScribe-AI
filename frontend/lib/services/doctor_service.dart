import '../models/doctor.dart';
import 'api_client.dart';

class DoctorService {
  final ApiClient _api;

  DoctorService(this._api);

  Future<List<Doctor>> fetchDoctors({String? specialization, String? name}) async {
    final query = <String, String>{
      if (specialization != null && specialization.isNotEmpty) 'specialization': specialization,
      if (name != null && name.isNotEmpty) 'name': name,
    };
    final json = await _api.getList('/doctors', query: query.isEmpty ? null : query);
    return json.map((dynamic e) => Doctor.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Doctor> fetchDoctorById(int id) async {
    final json = await _api.getJson('/doctors/$id');
    return Doctor.fromJson(json);
  }

  Future<Map<String, dynamic>> suggestDoctor(List<String> symptoms) {
    return _api.postJson('/ai/symptom-suggestion', {'symptoms': symptoms});
  }
}
