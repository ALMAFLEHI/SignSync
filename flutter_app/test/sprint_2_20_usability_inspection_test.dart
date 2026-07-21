import 'package:flutter/material.dart';
import 'package:flutter_app/controllers/banking_interaction_controller.dart';
import 'package:flutter_app/models/banking_interaction_session.dart';
import 'package:flutter_app/models/prediction_result.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/banking_interaction_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late QueryConfiguration configuration;

  setUpAll(() async {
    configuration = await QueryConfigurationService().load();
  });

  testWidgets('scenario 1 completes account problem and clears masked data', (
    tester,
  ) async {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    await _pumpWorkflow(tester, configuration, controller);

    await _tap(tester, const ValueKey('emit-account'));
    expect(find.byKey(const ValueKey('intent-confirmation-step')), findsOne);
    expect(find.text('Account'), findsWidgets);
    expect(find.text('Confirm Intent'), findsWidgets);
    expect(find.text('Try Again'), findsOne);
    expect(find.text('Cancel Interaction'), findsOne);

    await _tap(tester, const ValueKey('confirm-intent'));
    expect(_queryOptions(), findsNWidgets(4));
    expect(find.text('I have a problem with my account.'), findsOne);
    expect(
      tester
          .widget<FilledButton>(find.byKey(const ValueKey('query-continue')))
          .onPressed,
      isNull,
    );

    await _tap(tester, const ValueKey('query-option-account_problem'));
    await _tap(tester, const ValueKey('query-continue'));
    final accountField = find.byKey(
      const ValueKey('manual-field-account_number'),
    );
    expect(accountField, findsOne);
    expect(
      tester
          .widget<EditableText>(
            find.descendant(
              of: accountField,
              matching: find.byType(EditableText),
            ),
          )
          .obscureText,
      isTrue,
    );
    await tester.enterText(accountField, '1234561864');
    await _tap(tester, const ValueKey('manual-details-continue'));

    expect(find.byKey(const ValueKey('request-review-step')), findsOne);
    expect(find.text('I have a problem with my account.'), findsOne);
    expect(find.text('**** 1864'), findsOne);
    expect(find.text('1234561864'), findsNothing);

    await _tap(tester, const ValueKey('show-to-banker'));
    expect(find.byKey(const ValueKey('banker-request-view')), findsOne);
    expect(find.byKey(const ValueKey('banker-topic')), findsOne);
    expect(find.text('**** 1864'), findsOne);
    expect(find.text('Offline processing'), findsOne);
    expect(find.text('Session only'), findsOne);
    expect(find.textContaining('Confidence'), findsNothing);
    expect(find.textContaining('TFLite'), findsNothing);

    await _scrollDownAndTap(
      tester,
      find.byKey(const ValueKey('banker-clear-session')),
    );
    expect(controller.session.step, BankingWorkflowStep.recognition);
    expect(controller.session.hasActiveData, isFalse);
    expect(controller.session.manualFieldValues, isEmpty);
  });

  testWidgets('scenario 2 completes transfer and starts a clean interaction', (
    tester,
  ) async {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    await _pumpWorkflow(tester, configuration, controller);

    await _tap(tester, const ValueKey('emit-transfer'));
    await _tap(tester, const ValueKey('confirm-intent'));
    expect(_queryOptions(), findsNWidgets(4));
    expect(find.text('I want to transfer money to another account.'), findsOne);
    await _tap(tester, const ValueKey('query-option-transfer_money'));
    await _tap(tester, const ValueKey('query-continue'));

    final amountField = find.byKey(const ValueKey('manual-field-amount'));
    final beneficiaryField = find.byKey(
      const ValueKey('manual-field-beneficiary_account'),
    );
    await tester.enterText(amountField, '1500');
    await tester.enterText(beneficiaryField, '1234563321');
    expect(
      tester
          .widget<EditableText>(
            find.descendant(
              of: beneficiaryField,
              matching: find.byType(EditableText),
            ),
          )
          .obscureText,
      isTrue,
    );
    await _tap(tester, const ValueKey('manual-details-continue'));

    expect(find.text('1500'), findsOne);
    expect(find.text('**** 3321'), findsOne);
    expect(find.text('1234563321'), findsNothing);
    await _tap(tester, const ValueKey('show-to-banker'));
    expect(find.text('Transfer'), findsOne);
    expect(find.text('I want to transfer money to another account.'), findsOne);
    expect(find.text('1500'), findsOne);
    expect(find.text('**** 3321'), findsOne);

    await _scrollDownAndTap(
      tester,
      find.byKey(const ValueKey('banker-new-interaction')),
    );
    expect(find.byKey(const ValueKey('fake-banking-recognition')), findsOne);
    expect(controller.session.hasActiveData, isFalse);
    expect(controller.session.manualFieldValues, isEmpty);
    expect(find.text('1500'), findsNothing);
    expect(find.text('**** 3321'), findsNothing);
  });

  testWidgets(
    'scenario 3 omits empty document details and exposes the direct-skip gap',
    (tester) async {
      final controller = BankingInteractionController();
      addTearDown(controller.dispose);
      await _pumpWorkflow(tester, configuration, controller);

      await _tap(tester, const ValueKey('emit-document'));
      await _tap(tester, const ValueKey('confirm-intent'));
      expect(_queryOptions(), findsNWidgets(4));
      await _tap(tester, const ValueKey('query-option-document_status'));
      await _tap(tester, const ValueKey('query-continue'));

      // The frozen document mapping references one optional field, so the
      // current workflow offers that page before allowing an empty submission.
      expect(find.byKey(const ValueKey('manual-details-step')), findsOne);
      await _tap(tester, const ValueKey('manual-details-continue'));
      expect(find.byKey(const ValueKey('request-review-step')), findsOne);
      expect(
        find.text('I want to check whether my document was accepted.'),
        findsOne,
      );
      expect(
        find.byKey(const ValueKey('review-detail-document_type')),
        findsNothing,
      );

      await _tap(tester, const ValueKey('show-to-banker'));
      expect(find.text('Document'), findsOne);
      expect(
        find.byKey(const ValueKey('banker-detail-document_type')),
        findsNothing,
      );
      await _scrollDownAndTap(tester, find.text('Back to Review'));
      expect(find.byKey(const ValueKey('request-review-step')), findsOne);
      await _tap(tester, const ValueKey('review-start-over'));
      expect(find.byKey(const ValueKey('fake-banking-recognition')), findsOne);
      expect(controller.session.hasActiveData, isFalse);
    },
  );

  testWidgets('scenario 4 supports try again, cancel, and clean reopening', (
    tester,
  ) async {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    await _pumpWorkflow(tester, configuration, controller);

    await _tap(tester, const ValueKey('emit-complaint'));
    expect(find.text('Complaint'), findsWidgets);
    await _tap(tester, const ValueKey('confirmation-try-again'));
    expect(find.byKey(const ValueKey('fake-banking-recognition')), findsOne);
    expect(controller.session.hasActiveData, isFalse);

    await _tap(tester, const ValueKey('emit-complaint'));
    await _tap(tester, const ValueKey('confirm-intent'));
    await _tap(tester, const ValueKey('query-option-complaint_status'));
    await _tapText(tester, 'Cancel Interaction');
    expect(controller.session.step, BankingWorkflowStep.recognition);
    expect(controller.session.hasActiveData, isFalse);
    expect(controller.session.manualFieldValues, isEmpty);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    await _pumpWorkflow(tester, configuration, controller);
    expect(find.byKey(const ValueKey('fake-banking-recognition')), findsOne);
    expect(find.text('Complaint'), findsNothing);
  });
}

Future<void> _pumpWorkflow(
  WidgetTester tester,
  QueryConfiguration configuration,
  BankingInteractionController controller,
) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: SignSyncTheme.light,
      darkTheme: SignSyncTheme.dark,
      home: BankingInteractionPage(
        queryService: _FixedQueryService(configuration),
        controller: controller,
        recognitionBuilder: _recognitionBuilder,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Widget _recognitionBuilder(
  BuildContext context,
  ValueChanged<PredictionResult> onPrediction,
  VoidCallback onCancel,
) {
  return ListView(
    key: const ValueKey('fake-banking-recognition'),
    padding: const EdgeInsets.all(16),
    children: [
      for (final label in const <String>[
        'account',
        'transfer',
        'document',
        'complaint',
      ])
        FilledButton(
          key: ValueKey('emit-$label'),
          onPressed: () => onPrediction(_prediction(label)),
          child: Text('Recognize $label'),
        ),
      TextButton(
        key: const ValueKey('fake-recognition-cancel'),
        onPressed: onCancel,
        child: const Text('Cancel'),
      ),
    ],
  );
}

Future<void> _tap(WidgetTester tester, Key key) async {
  final finder = find.byKey(key);
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pump();
}

Future<void> _tapText(WidgetTester tester, String text) async {
  final finder = find.text(text);
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pump();
}

Future<void> _scrollDownAndTap(WidgetTester tester, Finder finder) async {
  for (var attempt = 0; attempt < 8 && finder.evaluate().isEmpty; attempt++) {
    await tester.drag(find.byType(Scrollable).last, const Offset(0, -350));
    await tester.pump();
  }
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pump();
}

Finder _queryOptions() {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    return key is ValueKey<String> && key.value.startsWith('query-option-');
  });
}

PredictionResult _prediction(String label) {
  final top = TopPrediction(label: label, probability: 0.95, index: 4);
  return PredictionResult(
    predictedLabel: label,
    confidence: 0.95,
    decision: PredictionDecision(
      accepted: true,
      displayLabel: label,
      confidenceThreshold: 0.80,
      minimumTop2Gap: 0.00,
      top2Gap: 0.50,
      reason: null,
    ),
    topPredictions: <TopPrediction>[top],
    rawTopPredictions: <TopPrediction>[top],
    rawOutputLength: 40,
    selectedMode: SignMode.bankingIntent,
    modelAsset: 'unchanged-test-model.tflite',
  );
}

class _FixedQueryService extends QueryConfigurationService {
  _FixedQueryService(this.configuration);

  final QueryConfiguration configuration;

  @override
  Future<QueryConfiguration> load() async => configuration;
}
