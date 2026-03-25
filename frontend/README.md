# Frontend (Flutter)

## Features Implemented

- OTP login flow
- KYC completion flow
- Doctor search by name and specialization
- Doctor profile with dynamic slots and booking
- Appointment tabs: Upcoming, Completed, Cancelled
- Payment simulation hook (`pay -> CONFIRMED`)
- Medical records list + upload PDF/image
- Pharmacy buy simulation from prescription notes
- English/Hindi language toggle
- AI symptom helper endpoint integration

## State Management

Uses `flutter_riverpod`:
- `authControllerProvider`
- `doctorFilterProvider` + `doctorsProvider`
- `appointmentControllerProvider`
- `recordControllerProvider`

## Navigation

Bottom navigation tabs:
- Home
- Appointments
- Records
- Profile

## Important Localhost Note

For Android emulator, update API base URL in `lib/core/constants.dart`:
- Use `http://10.0.2.2:8000` instead of `http://127.0.0.1:8000`

## Report Upload Input

- The app accepts an optional local file path in Records for report upload.
- This avoids native file-picker plugin requirements on restricted Windows setups.
