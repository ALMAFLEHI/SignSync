import 'package:flutter/material.dart';
import 'package:flutter_app/controllers/banking_interaction_controller.dart';
import 'package:flutter_app/models/banking_interaction_session.dart';
import 'package:flutter_app/models/prediction_result.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/banking_interaction_page.dart';
import 'package:flutter_app/ui/home_page.dart';
import 'package:flutter_app/ui/live_camera_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late QueryConfiguration configuration;

  setUpAll(() async {
    configuration = await QueryConfigurationService().load();
  });

  testWidgets('home opens the banking interaction workflow', (tester) async {
    await tester.pumpWidget(
      MaterialApp(theme: SignSyncTheme.light, home: const HomePage()),
    );

    final startButton = find.byKey(const ValueKey('start-banking-interaction'));
    final startControl = tester.widget<FilledButton>(startButton);
    expect(startControl.onPressed, isNotNull);
    startControl.onPressed!();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.byType(BankingInteractionPage), findsOneWidget);
    expect(find.text('Alphabet Mode'), findsNothing);
    expect(find.text('Number Mode'), findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  testWidgets('normal recognition automatically uses banking mode only', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: const Scaffold(
          body: LiveCameraPage(bankingOnly: true, embedded: true),
        ),
      ),
    );

    expect(find.byKey(const ValueKey('banking-mode-active')), findsOneWidget);
    expect(find.text('Banking signs only'), findsOneWidget);
    expect(find.text('Alphabet Mode'), findsNothing);
    expect(find.text('Number Mode'), findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  for (final themeMode in <ThemeMode>[ThemeMode.light, ThemeMode.dark]) {
    testWidgets('${themeMode.name} theme renders the guided workflow', (
      tester,
    ) async {
      final controller = BankingInteractionController();
      addTearDown(controller.dispose);
      await _pumpWorkflow(
        tester,
        configuration,
        controller,
        themeMode: themeMode,
      );

      await tester.tap(find.byKey(const ValueKey('emit-deposit')));
      await tester.pump();

      expect(
        find.byKey(const ValueKey('intent-confirmation-step')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'completes confirmation, exact query, review, banker, and reset',
    (tester) async {
      final controller = BankingInteractionController();
      addTearDown(controller.dispose);
      await _pumpWorkflow(tester, configuration, controller);

      await tester.tap(find.byKey(const ValueKey('emit-deposit')));
      await tester.pump();
      expect(
        find.byKey(const ValueKey('intent-confirmation-step')),
        findsOneWidget,
      );
      expect(find.text('Deposit'), findsWidgets);
      expect(find.text('Confidence: 95%'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('confirm-intent')));
      await tester.pump();
      expect(
        find.byKey(const ValueKey('query-selection-step')),
        findsOneWidget,
      );
      expect(_queryOptionFinder(), findsNWidgets(4));
      expect(
        tester
            .widget<FilledButton>(find.byKey(const ValueKey('query-continue')))
            .onPressed,
        isNull,
      );

      await tester.tap(
        find.byKey(const ValueKey('query-option-deposit_to_account')),
      );
      await tester.pump();
      expect(controller.session.selectedQuery?.id, 'deposit_to_account');
      expect(
        tester
            .widget<FilledButton>(find.byKey(const ValueKey('query-continue')))
            .onPressed,
        isNotNull,
      );
      await tester.tap(find.byKey(const ValueKey('query-continue')));
      await tester.pump();

      expect(find.byKey(const ValueKey('manual-field-amount')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('manual-field-account_type')),
        findsOneWidget,
      );
      await tester.enterText(
        find.byKey(const ValueKey('manual-field-amount')),
        '250.00',
      );
      await tester.tap(find.byKey(const ValueKey('manual-field-account_type')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Savings').last);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('manual-details-continue')));
      await tester.pump();

      expect(find.byKey(const ValueKey('request-review-step')), findsOneWidget);
      expect(
        find.text('I want to deposit money into a specific account.'),
        findsOneWidget,
      );
      expect(find.text('250.00'), findsOneWidget);
      expect(find.text('Savings'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('show-to-banker')));
      await tester.pump();

      expect(find.byKey(const ValueKey('banker-request-view')), findsOneWidget);
      expect(find.text('Customer Banking Request'), findsOneWidget);
      expect(
        find.text('I want to deposit money into a specific account.'),
        findsOneWidget,
      );
      expect(find.text('deposit_to_account'), findsNothing);
      expect(find.text('account_type'), findsNothing);
      expect(find.text('deposit'), findsNothing);
      await tester.scrollUntilVisible(
        find.textContaining('authorized bank staff'),
        250,
        scrollable: find.byType(Scrollable).last,
      );
      expect(find.textContaining('authorized bank staff'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('banker-new-interaction')));
      await tester.pump();
      expect(
        find.byKey(const ValueKey('fake-banking-recognition')),
        findsOneWidget,
      );
      expect(controller.session.step, BankingWorkflowStep.recognition);
      expect(controller.session.hasActiveData, isFalse);
      expect(controller.session.manualFieldValues, isEmpty);
      expect(find.text('250.00'), findsNothing);
      expect(controller.goBack(), isFalse);
    },
  );

  testWidgets(
    'Try Again rejects alphabet, digit, removed, and uncertain results',
    (tester) async {
      final controller = BankingInteractionController();
      addTearDown(controller.dispose);
      await _pumpWorkflow(tester, configuration, controller);

      for (final key in <String>[
        'emit-alphabet',
        'emit-digit',
        'emit-removed',
      ]) {
        await tester.tap(find.byKey(ValueKey(key)));
        await tester.pump();
        expect(
          find.byKey(const ValueKey('intent-confirmation-step')),
          findsNothing,
        );
        expect(
          find.text('This result is not a supported banking intent.'),
          findsOneWidget,
        );
        await tester.tap(
          find.byKey(const ValueKey('workflow-recognition-try-again')),
        );
        await tester.pump();
        expect(
          find.byKey(const ValueKey('banking-recognition-error')),
          findsNothing,
        );
      }

      await tester.tap(find.byKey(const ValueKey('emit-low-confidence')));
      await tester.pump();
      expect(
        find.text('The sign could not be recognized confidently.'),
        findsOneWidget,
      );
      expect(find.text('Try Again'), findsOneWidget);
      expect(controller.session.hasActiveData, isFalse);
    },
  );

  testWidgets('optional details may be empty and do not create review rows', (
    tester,
  ) async {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    await _pumpWorkflow(tester, configuration, controller);

    await tester.tap(find.byKey(const ValueKey('emit-transfer')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('confirm-intent')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('query-option-transfer_money')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('query-continue')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('manual-details-continue')));
    await tester.pump();

    expect(find.byKey(const ValueKey('request-review-step')), findsOneWidget);
    expect(find.byKey(const ValueKey('review-detail-amount')), findsNothing);
    expect(
      find.byKey(const ValueKey('review-detail-beneficiary_account')),
      findsNothing,
    );
  });

  testWidgets('missing local query content fails safely', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: BankingInteractionPage(
          queryService: _FailingQueryService(),
          recognitionBuilder: _fakeRecognitionBuilder,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('Local request content could not be loaded.'),
      findsOneWidget,
    );
    expect(find.text('Retry'), findsOneWidget);
    expect(find.text('Return Home'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pumpWorkflow(
  WidgetTester tester,
  QueryConfiguration configuration,
  BankingInteractionController controller, {
  ThemeMode themeMode = ThemeMode.light,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: SignSyncTheme.light,
      darkTheme: SignSyncTheme.dark,
      themeMode: themeMode,
      home: BankingInteractionPage(
        queryService: _FixedQueryService(configuration),
        controller: controller,
        recognitionBuilder: _fakeRecognitionBuilder,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Widget _fakeRecognitionBuilder(
  BuildContext context,
  ValueChanged<PredictionResult> onPrediction,
  VoidCallback onCancel,
) {
  return ListView(
    key: const ValueKey('fake-banking-recognition'),
    padding: const EdgeInsets.all(16),
    children: [
      const Text('Banking signs only'),
      FilledButton(
        key: const ValueKey('emit-deposit'),
        onPressed: () => onPrediction(_prediction('deposit')),
        child: const Text('Recognize deposit'),
      ),
      FilledButton(
        key: const ValueKey('emit-transfer'),
        onPressed: () => onPrediction(_prediction('transfer')),
        child: const Text('Recognize transfer'),
      ),
      FilledButton(
        key: const ValueKey('emit-alphabet'),
        onPressed: () => onPrediction(_prediction('A')),
        child: const Text('Reject alphabet'),
      ),
      FilledButton(
        key: const ValueKey('emit-digit'),
        onPressed: () => onPrediction(_prediction('7')),
        child: const Text('Reject digit'),
      ),
      FilledButton(
        key: const ValueKey('emit-removed'),
        onPressed: () => onPrediction(_prediction('address_change')),
        child: const Text('Reject removed label'),
      ),
      FilledButton(
        key: const ValueKey('emit-low-confidence'),
        onPressed: () => onPrediction(
          _prediction('deposit', confidence: 0.40, accepted: false),
        ),
        child: const Text('Reject uncertain result'),
      ),
      TextButton(onPressed: onCancel, child: const Text('Cancel')),
    ],
  );
}

Finder _queryOptionFinder() {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    return key is ValueKey<String> && key.value.startsWith('query-option-');
  });
}

PredictionResult _prediction(
  String label, {
  double confidence = 0.95,
  bool accepted = true,
}) {
  final top = TopPrediction(label: label, probability: confidence, index: 36);
  return PredictionResult(
    predictedLabel: label,
    confidence: confidence,
    decision: PredictionDecision(
      accepted: accepted,
      displayLabel: accepted ? label : '',
      confidenceThreshold: 0.90,
      minimumTop2Gap: 0.00,
      top2Gap: 0.50,
      reason: accepted ? null : 'Below confidence threshold.',
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

class _FailingQueryService extends QueryConfigurationService {
  @override
  Future<QueryConfiguration> load() async {
    throw const QueryConfigurationException('Invalid local test content.');
  }
}
