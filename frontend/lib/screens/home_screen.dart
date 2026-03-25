import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants.dart';
import '../models/doctor.dart';
import '../state/doctor_controller.dart';
import '../state/app_providers.dart';
import '../widgets/doctor_card.dart';
import 'doctor_profile_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _symptomController = TextEditingController();
  String _aiSuggestion = '';

  @override
  void dispose() {
    _searchController.dispose();
    _symptomController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final doctorsAsync = ref.watch(doctorsProvider);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Text('Find Your Doctor', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            TextField(
              controller: _searchController,
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search by name'),
              onChanged: (String value) {
                final current = ref.read(doctorFilterProvider);
                ref.read(doctorFilterProvider.notifier).state = DoctorFilter(query: value, specialization: current.specialization);
              },
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 44,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: AppConstants.specializations.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (BuildContext context, int index) {
                  final category = AppConstants.specializations[index];
                  return ActionChip(
                    label: Text(category),
                    onPressed: () {
                      final current = ref.read(doctorFilterProvider);
                      ref.read(doctorFilterProvider.notifier).state = DoctorFilter(query: current.query, specialization: category);
                    },
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _symptomController,
              decoration: InputDecoration(
                hintText: 'AI symptom helper (e.g. fever cough)',
                suffixIcon: IconButton(
                  icon: const Icon(Icons.auto_awesome),
                  onPressed: () async {
                    final service = ref.read(doctorServiceProvider);
                    final result = await service.suggestDoctor(_symptomController.text.split(' '));
                    setState(() => _aiSuggestion = '${result['suggestion']}');
                  },
                ),
              ),
            ),
            if (_aiSuggestion.isNotEmpty) ...<Widget>[
              const SizedBox(height: 8),
              Text(_aiSuggestion, style: const TextStyle(color: Colors.teal, fontWeight: FontWeight.w600)),
            ],
            const SizedBox(height: 12),
            Expanded(
              child: doctorsAsync.when(
                data: (List<Doctor> doctors) {
                  return ListView.builder(
                    itemCount: doctors.length,
                    itemBuilder: (BuildContext context, int index) {
                      final doctor = doctors[index];
                      return DoctorCard(
                        doctor: doctor,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute<void>(builder: (_) => DoctorProfileScreen(doctorId: doctor.id)),
                        ),
                      );
                    },
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (Object e, StackTrace st) => Center(child: Text(e.toString())),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
