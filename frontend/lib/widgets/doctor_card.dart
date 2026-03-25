import 'package:flutter/material.dart';

import '../models/doctor.dart';

class DoctorCard extends StatelessWidget {
  const DoctorCard({super.key, required this.doctor, required this.onTap});

  final Doctor doctor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: ListTile(
        onTap: onTap,
        title: Text(doctor.name, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('${doctor.specialization} • ${doctor.experience} yrs'),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text('₹${doctor.fees.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.w700)),
            Text('⭐ ${doctor.rating.toStringAsFixed(1)}'),
          ],
        ),
      ),
    );
  }
}
