import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/app_theme.dart';
import 'core/strings.dart';
import 'screens/app_shell.dart';
import 'screens/kyc_screen.dart';
import 'screens/login_screen.dart';
import 'state/app_providers.dart';
import 'state/auth_controller.dart';

void main() {
  runApp(const ProviderScope(child: PatientApp()));
}

class PatientApp extends ConsumerWidget {
  const PatientApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final locale = ref.watch(localeProvider);
    final strings = AppStrings(locale);

    Widget home;
    if (auth.patient == null) {
      home = const LoginScreen();
    } else if (!auth.patient!.kycVerified) {
      home = const KycScreen();
    } else {
      home = const AppShell();
    }

    return MaterialApp(
      title: strings.t('appTitle'),
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      locale: locale,
      home: home,
    );
  }
}
