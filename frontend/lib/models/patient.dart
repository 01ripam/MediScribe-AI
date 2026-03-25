class Patient {
  final int id;
  final String? name;
  final int? age;
  final String? gender;
  final String phone;
  final String? govtIdHash;
  final bool kycVerified;

  const Patient({
    required this.id,
    required this.name,
    required this.age,
    required this.gender,
    required this.phone,
    required this.govtIdHash,
    required this.kycVerified,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'] as int,
      name: json['name'] as String?,
      age: json['age'] as int?,
      gender: json['gender'] as String?,
      phone: json['phone'] as String,
      govtIdHash: json['govt_id_hash'] as String?,
      kycVerified: json['kyc_verified'] as bool,
    );
  }
}
