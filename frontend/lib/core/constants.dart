class AppConstants {
  // Configure with --dart-define=API_BASE_URL=https://api.your-domain.com
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
  static const List<String> specializations = <String>[
    'General Medicine',
    'Dental',
    'Orthopedic',
    'Dermatology',
    'Ophthalmology',
  ];
}
