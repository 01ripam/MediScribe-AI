import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../state/app_providers.dart';
import '../state/record_controller.dart';

class RecordsScreen extends ConsumerStatefulWidget {
  const RecordsScreen({super.key});

  @override
  ConsumerState<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends ConsumerState<RecordsScreen> {
  final TextEditingController _diagnosisController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  final TextEditingController _reportPathController = TextEditingController();
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(() => ref.read(recordControllerProvider.notifier).refresh());
  }

  @override
  void dispose() {
    _diagnosisController.dispose();
    _notesController.dispose();
    _reportPathController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final recordsAsync = ref.watch(recordControllerProvider);
    final pharmacy = ref.read(pharmacyServiceProvider);

    return SafeArea(
      child: recordsAsync.when(
        data: (records) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: <Widget>[
              Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Text('Upload Medical Report', style: TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _diagnosisController,
                        decoration: const InputDecoration(labelText: 'Diagnosis'),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _notesController,
                        maxLines: 2,
                        decoration: const InputDecoration(labelText: 'Doctor Notes'),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _reportPathController,
                        decoration: const InputDecoration(
                          labelText: 'Report file path (optional)',
                          hintText: 'Example: C:/reports/lab.pdf',
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: <Widget>[
                          Expanded(
                            child: FilledButton(
                              onPressed: () async {
                                await ref.read(recordControllerProvider.notifier).addRecord(
                                      diagnosis: _diagnosisController.text.trim(),
                                      doctorNotes: _notesController.text.trim(),
                                      recordDate: DateTime.now().toIso8601String().split('T').first,
                                      filePath: _reportPathController.text.trim().isEmpty
                                          ? null
                                          : _reportPathController.text.trim(),
                                    );
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Record uploaded')));
                                }
                              },
                              child: const Text('Upload Record'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.tonalIcon(
                            onPressed: () async {
                              final captured = await _imagePicker.pickImage(source: ImageSource.camera, imageQuality: 85);
                              if (captured == null) {
                                return;
                              }

                              final diagnosis = _diagnosisController.text.trim().isEmpty
                                  ? 'Scanned hardcopy record'
                                  : _diagnosisController.text.trim();
                              final notes = _notesController.text.trim().isEmpty
                                  ? 'Uploaded using camera scan'
                                  : _notesController.text.trim();

                              await ref.read(recordControllerProvider.notifier).addRecord(
                                    diagnosis: diagnosis,
                                    doctorNotes: notes,
                                    recordDate: DateTime.now().toIso8601String().split('T').first,
                                    filePath: captured.path,
                                  );

                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Scanned record uploaded')));
                              }
                            },
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Scan'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              if (records.isEmpty)
                const Center(child: Padding(padding: EdgeInsets.all(20), child: Text('No medical records available'))),
              ...records.map((record) {
                final medicines = pharmacy.extractMedicines(record.doctorNotes);
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(record.diagnosis, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                        const SizedBox(height: 6),
                        Text('Date: ${record.date}'),
                        Text('Notes: ${record.doctorNotes}'),
                        const SizedBox(height: 8),
                        const Text('Medicines', style: TextStyle(fontWeight: FontWeight.w700)),
                        Wrap(spacing: 8, children: medicines.map((m) => Chip(label: Text(m))).toList()),
                        const SizedBox(height: 8),
                        FilledButton(
                          onPressed: () async {
                            final msg = await pharmacy.placeOrder(medicine: medicines.first);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
                            }
                          },
                          child: const Text('Buy Medicine'),
                        ),
                      ],
                    ),
                  ),
                );
              }),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (Object e, StackTrace _) => Center(child: Text(e.toString())),
      ),
    );
  }
}
