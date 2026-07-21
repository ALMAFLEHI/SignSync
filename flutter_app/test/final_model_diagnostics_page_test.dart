import 'package:flutter/material.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_app/ui/final_model_diagnostics_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Final Model Diagnostics reports the frozen contract as PASS', (
    tester,
  ) async {
    final metadata = await LabelService().load();
    await tester.pumpWidget(
      MaterialApp(
        home: FinalModelDiagnosticsPage(
          loader: () async => FinalModelDiagnosticsData(
            metadata: metadata,
            modelLoaded: true,
            contractValidated: true,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Contract validation PASS'), findsOneWidget);
    expect(find.text('[1, 756]'), findsOneWidget);
    expect(find.text('[1, 40]'), findsOneWidget);
    expect(find.text('40 banking intents'), findsOneWidget);
    expect(
      find.text(AppConfig.bankingIntentConfidenceThreshold.toStringAsFixed(2)),
      findsOneWidget,
    );
    await tester.scrollUntilVisible(
      find.text('PASS - exact 40-label order'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('PASS - exact 40-label order'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('com.example.flutter_app'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('com.example.flutter_app'), findsOneWidget);
    expect(find.textContaining('customer'), findsNothing);
  });

  testWidgets('Final Model Diagnostics exposes a local configuration failure', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: FinalModelDiagnosticsPage(
          loader: () async => throw StateError('test contract mismatch'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Contract validation FAIL'), findsOneWidget);
    expect(find.textContaining('test contract mismatch'), findsOneWidget);
  });
}
