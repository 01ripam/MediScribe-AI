import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/auth_controller.dart';

class KycScreen extends ConsumerStatefulWidget {
  const KycScreen({super.key});

  @override
  ConsumerState<KycScreen> createState() => _KycScreenState();
}

class _KycScreenState extends ConsumerState<KycScreen> {
  final _nameController = TextEditingController();
  final _ageController = TextEditingController();
  final _genderController = TextEditingController();
  final _idController = TextEditingController();
  String _idType = 'AADHAAR';

  @override
  void dispose() {
    _nameController.dispose();
    _ageController.dispose();
    _genderController.dispose();
    _idController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final auth = ref.read(authControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('KYC Verification')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: ListView(
          children: <Widget>[
            const Text('One patient = one account. Government ID is hashed before storage.'),
            const SizedBox(height: 16),
            TextField(controller: _nameController, decoration: const InputDecoration(labelText: 'Name')),
            const SizedBox(height: 12),
            TextField(controller: _ageController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Age')),
            const SizedBox(height: 12),
            TextField(controller: _genderController, decoration: const InputDecoration(labelText: 'Gender')),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _idType,
              items: const <String>['AADHAAR', 'PAN', 'VOTER_ID', 'OTHER']
                  .map((String value) => DropdownMenuItem<String>(value: value, child: Text(value)))
                  .toList(),
              onChanged: (String? value) => setState(() => _idType = value ?? 'AADHAAR'),
              decoration: const InputDecoration(labelText: 'Government ID Type'),
            ),
            const SizedBox(height: 12),
            TextField(controller: _idController, decoration: const InputDecoration(labelText: 'Government ID Number')),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: authState.loading
                  ? null
                  : () => auth.completeKyc(
                        name: _nameController.text.trim(),
                        age: int.tryParse(_ageController.text.trim()) ?? 0,
                        gender: _genderController.text.trim(),
                        govtId: _idController.text.trim(),
                        govtIdType: _idType,
                      ),
              child: const Text('Submit KYC'),
            ),
            const SizedBox(height: 16),
            if (authState.error != null)
              Text(authState.error!, style: const TextStyle(color: Colors.red)),
          ],
        ),
      ),
    );
  }
}
