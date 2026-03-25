class MedicalRecord {
  final int id;
  final int patientId;
  final int? doctorId;
  final String date;
  final String diagnosis;
  final String prescriptionUrl;
  final String doctorNotes;

  const MedicalRecord({
    required this.id,
    required this.patientId,
    required this.doctorId,
    required this.date,
    required this.diagnosis,
    required this.prescriptionUrl,
    required this.doctorNotes,
  });

  factory MedicalRecord.fromJson(Map<String, dynamic> json) {
    return MedicalRecord(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      doctorId: json['doctor_id'] as int?,
      date: json['date'] as String,
      diagnosis: json['diagnosis'] as String,
      prescriptionUrl: json['prescription_url'] as String,
      doctorNotes: json['doctor_notes'] as String,
    );
  }
}
