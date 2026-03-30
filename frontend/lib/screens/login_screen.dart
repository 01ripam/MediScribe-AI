import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/auth_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _otpController = TextEditingController();

  String _normalizeErrorMessage(String raw) {
    final lower = raw.toLowerCase();
    if (lower.contains('invalid_otp') || lower.contains('invalid or expired otp')) {
      return 'Enter correct OTP';
    }
    if (lower.contains('phone') || lower.contains('validation error')) {
      return 'Please enter correct number';
    }
    return raw;
  }

  Future<void> _showErrorDialog(String message) async {
    await showDialog<void>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Error'),
          content: Text(message),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendOtp() async {
    final auth = ref.read(authControllerProvider.notifier);
    final phone = _phoneController.text.trim();
    final isValidPhone = RegExp(r'^\d{10}$').hasMatch(phone);

    if (!isValidPhone) {
      await _showErrorDialog('Please enter correct number');
      return;
    }

    await auth.login(phone);
  }

  Future<void> _verifyOtp() async {
    final auth = ref.read(authControllerProvider.notifier);
    final phone = _phoneController.text.trim();
    final otp = _otpController.text.trim();

    if (!RegExp(r'^\d{10}$').hasMatch(phone)) {
      await _showErrorDialog('Please enter correct number');
      return;
    }
    if (!RegExp(r'^\d{6}$').hasMatch(otp)) {
      await _showErrorDialog('Enter correct OTP');
      return;
    }

    await auth.verifyOtp(phone: phone, otp: otp);
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    ref.listen<AuthState>(authControllerProvider, (AuthState? previous, AuthState next) {
      if (!mounted) {
        return;
      }
      final hasNewError = next.error != null && next.error != previous?.error;
      if (hasNewError) {
        _showErrorDialog(_normalizeErrorMessage(next.error!));
      }
    });

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const SizedBox(height: 24),
              const Text('Patient Login', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              const Text('Secure OTP login with mandatory KYC verification.'),
              const SizedBox(height: 24),
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(labelText: 'Phone Number'),
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: authState.loading
                    ? null
                    : _sendOtp,
                child: const Text('Send OTP'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _otpController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'OTP'),
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: authState.loading
                    ? null
                    : _verifyOtp,
                child: const Text('Verify OTP'),
              ),
              const SizedBox(height: 16),
              if (authState.message != null)
                Text(authState.message!, style: const TextStyle(color: Colors.teal, fontWeight: FontWeight.w600)),
              if (authState.error != null)
                Text(authState.error!, style: const TextStyle(color: Colors.red)),
            ],
          ),
        ),
      ),
    );
  }
}
