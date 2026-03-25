import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/medical_record.dart';
import '../core/constants.dart';
import 'api_client.dart';

class RecordService {
  final ApiClient _api;
  final http.Client _httpClient;

  RecordService(this._api, {http.Client? httpClient}) : _httpClient = httpClient ?? http.Client();

  Future<List<MedicalRecord>> fetchRecords(int patientId) async {
    final json = await _api.getList('/records', query: {'patient_id': '$patientId'});
    return json.map((dynamic e) => MedicalRecord.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<MedicalRecord> addRecord({
    required int patientId,
    required String diagnosis,
    required String doctorNotes,
    required String recordDate,
    int? doctorId,
    String? filePath,
  }) async {
    final uri = Uri.parse('${AppConstants.apiBaseUrl}/records');
    final request = http.MultipartRequest('POST', uri)
      ..fields['patient_id'] = '$patientId'
      ..fields['diagnosis'] = diagnosis
      ..fields['doctor_notes'] = doctorNotes
      ..fields['record_date'] = recordDate;

    if (doctorId != null) {
      request.fields['doctor_id'] = '$doctorId';
    }
    if (filePath != null && filePath.isNotEmpty) {
      request.files.add(await http.MultipartFile.fromPath('report', filePath));
    }

    final streamed = await _httpClient.send(request);
    final response = await http.Response.fromStream(streamed);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Upload failed (${response.statusCode}): ${response.body}');
    }
    return MedicalRecord.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }
}
