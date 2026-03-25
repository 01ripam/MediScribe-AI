import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/app_providers.dart';
import '../state/auth_controller.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final patient = auth.patient;

    if (patient == null) {
      return const Center(child: Text('Please login'));
    }

    return SafeArea(
      child: Column(
        children: <Widget>[
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: <Widget>[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(patient.name ?? 'Unnamed Patient', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 20)),
                        const SizedBox(height: 6),
                        Text('Phone: ${patient.phone}'),
                        Text('Age: ${patient.age ?? '-'}'),
                        Text('Gender: ${patient.gender ?? '-'}'),
                        Text('KYC Verified: ${patient.kycVerified ? 'Yes' : 'No'}'),
                        const SizedBox(height: 6),
                        Text('Govt ID Hash: ${patient.govtIdHash ?? 'Not set'}'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const Text('Language', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: <Widget>[
                    ActionChip(
                      label: const Text('English'),
                      onPressed: () => ref.read(localeProvider.notifier).state = const Locale('en'),
                    ),
                    ActionChip(
                      label: const Text('हिन्दी'),
                      onPressed: () => ref.read(localeProvider.notifier).state = const Locale('hi'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () => ref.read(authControllerProvider.notifier).signOut(),
                child: const Text('Sign Out'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
