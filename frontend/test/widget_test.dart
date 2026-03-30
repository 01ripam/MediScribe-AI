import 'package:flutter_test/flutter_test.dart';

import 'package:patient_side_app/main.dart';

void main() {
  testWidgets('App shell boots', (WidgetTester tester) async {
    await tester.pumpWidget(const PatientApp());
    expect(find.byType(PatientApp), findsOneWidget);
  });
}
