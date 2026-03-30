class AppConstants {
  // Configure with --dart-define=API_BASE_URL=https://api.your-domain.com
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://192.168.1.20:8001',
  );
  static const String appApiKey = String.fromEnvironment(
    'APP_API_KEY',
    defaultValue: 'replace_with_very_long_random_key_1234567890',
  );
  static const List<String> specializations = <String>[
    'General Medicine',
    'Dental',
    'Orthopedic',
    'Dermatology',
    'Ophthalmology',
  ];
}
