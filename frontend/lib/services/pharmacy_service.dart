class PharmacyService {
  Future<String> placeOrder({required String medicine}) async {
    await Future<void>.delayed(const Duration(milliseconds: 700));
    return 'Order placed for $medicine. Expected delivery in 24 hours.';
  }

  List<String> extractMedicines(String doctorNotes) {
    final lower = doctorNotes.toLowerCase();
    if (lower.contains('physiotherapy')) {
      return <String>['Pain Relief Gel', 'Vitamin D3', 'Calcium Tablets'];
    }
    if (lower.contains('antibiotic')) {
      return <String>['Amoxicillin', 'Probiotic Capsule'];
    }
    return <String>['Paracetamol', 'Multivitamin'];
  }
}
