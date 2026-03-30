class Doctor {
  final int id;
  final String name;
  final String specialization;
  final int experience;
  final double fees;
  final double rating;
  final String bio;
  final List<String> availableSlots;
  final List<String> busySlots;

  const Doctor({
    required this.id,
    required this.name,
    required this.specialization,
    required this.experience,
    required this.fees,
    required this.rating,
    required this.bio,
    required this.availableSlots,
    required this.busySlots,
  });

  factory Doctor.fromJson(Map<String, dynamic> json) {
    return Doctor(
      id: json['id'] as int,
      name: json['name'] as String,
      specialization: json['specialization'] as String,
      experience: json['experience'] as int,
      fees: (json['fees'] as num).toDouble(),
      rating: (json['rating'] as num).toDouble(),
      bio: json['bio'] as String,
      availableSlots: (json['available_slots'] as List<dynamic>).cast<String>(),
      busySlots: ((json['busy_slots'] as List<dynamic>?) ?? const <dynamic>[]).cast<String>(),
    );
  }
}
