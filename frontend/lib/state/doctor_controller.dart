import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/doctor.dart';
import 'app_providers.dart';

class DoctorFilter {
  final String query;
  final String specialization;

  const DoctorFilter({this.query = '', this.specialization = ''});
}

final doctorFilterProvider = StateProvider<DoctorFilter>((ref) => const DoctorFilter());

final doctorsProvider = FutureProvider<List<Doctor>>((ref) async {
  final filter = ref.watch(doctorFilterProvider);
  return ref.read(doctorServiceProvider).fetchDoctors(
        specialization: filter.specialization,
        name: filter.query,
      );
});
