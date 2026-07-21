import 'package:flutter/material.dart';
import 'package:flutter_app/controllers/banking_interaction_controller.dart';
import 'package:flutter_app/models/manual_field_config.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/banking_workflow/manual_details_step.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('renders all field types with validation, masking, and pickers', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1000, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    final intent = _intentWithAllFieldTypes();
    controller.acceptPrediction(intent: intent, confidence: 0.90);
    controller.confirmIntent();
    controller.selectQuery(intent.queries.single);
    controller.continueFromQuerySelection();

    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: Scaffold(
          body: AnimatedBuilder(
            animation: controller,
            builder: (context, _) => ManualDetailsStep(
              key: const ValueKey('all-manual-fields'),
              controller: controller,
              session: controller.session,
              onContinue: controller.submitManualDetails,
              onBack: controller.goBack,
              onCancel: controller.reset,
            ),
          ),
        ),
      ),
    );

    for (final id in <String>[
      'text',
      'multiline',
      'number',
      'masked',
      'amount',
      'date',
      'time',
      'select',
    ]) {
      expect(find.byKey(ValueKey('manual-field-$id')), findsOneWidget);
    }

    await tester.tap(find.byKey(const ValueKey('manual-details-continue')));
    await tester.pump();
    expect(find.text('Please complete the required field.'), findsNWidgets(8));

    await tester.enterText(
      find.byKey(const ValueKey('manual-field-amount')),
      '12.345',
    );
    expect(controller.session.manualFieldValues['amount'] ?? '', isEmpty);
    await tester.enterText(
      find.byKey(const ValueKey('manual-field-amount')),
      '12.34',
    );
    expect(controller.session.manualFieldValues['amount'], '12.34');

    await tester.enterText(
      find.byKey(const ValueKey('manual-field-masked')),
      '12345678',
    );
    final maskedEditable = find.descendant(
      of: find.byKey(const ValueKey('manual-field-masked')),
      matching: find.byType(EditableText),
    );
    expect(tester.widget<EditableText>(maskedEditable).obscureText, isTrue);
    await tester.tap(find.byKey(const ValueKey('manual-field-reveal-masked')));
    await tester.pump();
    expect(tester.widget<EditableText>(maskedEditable).obscureText, isFalse);

    await tester.tap(find.byTooltip('Date *'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    expect(
      controller.session.manualFieldValues['date'],
      matches(RegExp(r'^\d{4}-\d{2}-\d{2}$')),
    );

    await tester.tap(find.byTooltip('Time *'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    expect(
      controller.session.manualFieldValues['time'],
      matches(RegExp(r'^\d{2}:\d{2}$')),
    );

    await tester.tap(find.byKey(const ValueKey('manual-field-select')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Savings').last);
    await tester.pumpAndSettle();
    expect(controller.session.manualFieldValues['select'], 'Savings');
  });
}

BankingIntentConfig _intentWithAllFieldTypes() {
  ManualFieldConfig field(
    String id,
    String label,
    ManualFieldType type, {
    List<String> options = const <String>[],
    bool sensitive = false,
    bool displayMasked = false,
  }) {
    return ManualFieldConfig(
      id: id,
      label: label,
      type: type,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: type == ManualFieldType.multilineText ? 120 : null,
      options: options,
      sensitive: sensitive,
      displayMasked: displayMasked,
    );
  }

  final fields = <ManualFieldConfig>[
    field('text', 'Text', ManualFieldType.text),
    field('multiline', 'Notes', ManualFieldType.multilineText),
    field('number', 'Number', ManualFieldType.number),
    field(
      'masked',
      'Masked number',
      ManualFieldType.maskedNumber,
      sensitive: true,
      displayMasked: true,
    ),
    field('amount', 'Amount', ManualFieldType.amount),
    field('date', 'Date', ManualFieldType.date),
    field('time', 'Time', ManualFieldType.time),
    field(
      'select',
      'Account type',
      ManualFieldType.select,
      options: <String>['Current', 'Savings'],
    ),
  ];
  return BankingIntentConfig(
    id: 'test',
    displayName: 'Test',
    description: 'All fields',
    queries: <BankingQueryOption>[
      BankingQueryOption(
        id: 'all_fields',
        text: 'All fields',
        manualFieldIds: fields.map((field) => field.id).toList(growable: false),
      ),
    ],
    manualFields: fields,
  );
}
