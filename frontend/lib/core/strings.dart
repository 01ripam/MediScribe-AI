import 'package:flutter/material.dart';

class AppStrings {
  final Locale locale;
  AppStrings(this.locale);

  static const Map<String, Map<String, String>> _localized = {
    'en': {
      'appTitle': 'CareBridge Patient',
      'home': 'Home',
      'appointments': 'Appointments',
      'records': 'Records',
      'profile': 'Profile',
      'requestAppointment': 'Request Appointment',
      'buyMedicine': 'Buy Medicine',
      'login': 'Login',
      'verifyOtp': 'Verify OTP',
      'completeKyc': 'Complete KYC',
    },
    'hi': {
      'appTitle': 'केयरब्रिज पेशेंट',
      'home': 'होम',
      'appointments': 'अपॉइंटमेंट',
      'records': 'रिकॉर्ड्स',
      'profile': 'प्रोफाइल',
      'requestAppointment': 'अपॉइंटमेंट अनुरोध',
      'buyMedicine': 'दवा खरीदें',
      'login': 'लॉगिन',
      'verifyOtp': 'ओटीपी सत्यापित करें',
      'completeKyc': 'केवाईसी पूरा करें',
    },
  };

  String t(String key) {
    return _localized[locale.languageCode]?[key] ?? _localized['en']![key] ?? key;
  }
}
