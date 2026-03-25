import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/medical_record.dart';
import 'app_providers.dart';
import 'auth_controller.dart';

class RecordController extends StateNotifier<AsyncValue<List<MedicalRecord>>> {
  RecordController(this.ref) : super(const AsyncValue.data(<MedicalRecord>[]));

  final Ref ref;

  Future<void> refresh() async {
    final patientId = ref.read(authControllerProvider).patient?.id;
    if (patientId == null) {
      state = const AsyncValue.data(<MedicalRecord>[]);
      return;
    }
    state = const AsyncValue.loading();
    try {
      final records = await ref.read(recordServiceProvider).fetchRecords(patientId);
      state = AsyncValue.data(records);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> addRecord({
    required String diagnosis,
    required String doctorNotes,
    required String recordDate,
    String? filePath,
  }) async {
    final patientId = ref.read(authControllerProvider).patient?.id;
    if (patientId == null) {
      return;
    }
    await ref.read(recordServiceProvider).addRecord(
          patientId: patientId,
          diagnosis: diagnosis,
          doctorNotes: doctorNotes,
          recordDate: recordDate,
          filePath: filePath,
        );
    await refresh();
  }
}

final recordControllerProvider = StateNotifierProvider<RecordController, AsyncValue<List<MedicalRecord>>>((ref) {
  return RecordController(ref);
});
