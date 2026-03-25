import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/constants.dart';

class ApiClient {
  final http.Client _client;

  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  Future<Map<String, dynamic>> getJson(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse('${AppConstants.apiBaseUrl}$path').replace(queryParameters: query);
    final response = await _client.get(uri, headers: _headers());
    _throwIfError(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getList(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse('${AppConstants.apiBaseUrl}$path').replace(queryParameters: query);
    final response = await _client.get(uri, headers: _headers());
    _throwIfError(response);
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> postJson(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('${AppConstants.apiBaseUrl}$path');
    final response = await _client.post(uri, headers: _headers(jsonBody: true), body: jsonEncode(body));
    _throwIfError(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> patchJson(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('${AppConstants.apiBaseUrl}$path');
    final response = await _client.patch(uri, headers: _headers(jsonBody: true), body: jsonEncode(body));
    _throwIfError(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Map<String, String> _headers({bool jsonBody = false}) {
    return <String, String>{
      'Accept': 'application/json',
      if (jsonBody) 'Content-Type': 'application/json',
    };
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }
    throw Exception('Request failed (${response.statusCode}): ${response.body}');
  }
}
