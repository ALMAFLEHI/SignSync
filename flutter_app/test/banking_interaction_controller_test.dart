import 'package:flutter_app/controllers/banking_interaction_controller.dart';
import 'package:flutter_app/models/banking_interaction_session.dart';
import 'package:flutter_app/models/manual_field_config.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late QueryConfiguration configuration;

  setUpAll(() async {
    configuration = await QueryConfigurationService().load();
  });

  test(
    'runs the configured intent, query, optional details, and reset flow',
    () {
      final controller = BankingInteractionController();
      addTearDown(controller.dispose);
      final transfer = _intent(configuration, 'transfer');
      final deposit = _intent(configuration, 'deposit');

      controller.acceptPrediction(intent: transfer, confidence: 0.91);
      expect(controller.session.step, BankingWorkflowStep.confirmation);
      expect(controller.session.detectedIntent?.id, 'transfer');

      controller.confirmIntent();
      expect(controller.session.step, BankingWorkflowStep.querySelection);
      expect(transfer.queries, hasLength(4));
      expect(controller.continueFromQuerySelection(), isFalse);
      expect(
        () => controller.selectQuery(deposit.queries.first),
        throwsArgumentError,
      );

      final transferMoney = transfer.queries.firstWhere(
        (query) => query.id == 'transfer_money',
      );
      controller.selectQuery(transferMoney);
      expect(controller.session.selectedQuery?.id, 'transfer_money');
      expect(controller.selectedManualFields.map((field) => field.id), <String>[
        'amount',
        'beneficiary_account',
      ]);
      expect(controller.continueFromQuerySelection(), isTrue);
      expect(controller.session.step, BankingWorkflowStep.manualDetails);

      // Both configured fields are optional and may be omitted.
      expect(controller.submitManualDetails(), isTrue);
      expect(controller.session.step, BankingWorkflowStep.review);
      expect(controller.populatedDetails, isEmpty);

      controller.showToBanker();
      expect(controller.session.step, BankingWorkflowStep.bankerView);
      controller.reset();

      expect(controller.session.step, BankingWorkflowStep.recognition);
      expect(controller.session.hasActiveData, isFalse);
      expect(controller.session.manualFieldValues, isEmpty);
      expect(controller.session.validationErrors, isEmpty);
      expect(controller.goBack(), isFalse);
    },
  );

  test('validates every supported field type and masks sensitive values', () {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    final intent = _allFieldTypesIntent();

    controller.acceptPrediction(intent: intent, confidence: 0.90);
    controller.confirmIntent();
    controller.selectQuery(intent.queries.single);
    expect(controller.continueFromQuerySelection(), isTrue);
    expect(controller.selectedManualFields, hasLength(8));

    expect(controller.submitManualDetails(), isFalse);
    expect(
      controller.session.validationErrors.keys,
      containsAll(<String>[
        'name',
        'reference',
        'amount',
        'date',
        'time',
        'type',
      ]),
    );

    controller.updateManualField('name', 'Customer');
    controller.updateManualField('notes', 'Optional note');
    controller.updateManualField('reference', '12A');
    controller.updateManualField('account', '12345678');
    controller.updateManualField('amount', '1.234');
    controller.updateManualField('date', '2026-02-30');
    controller.updateManualField('time', '24:00');
    controller.updateManualField('type', 'Unknown');
    expect(controller.submitManualDetails(), isFalse);
    expect(
      controller.session.validationErrors['reference'],
      'Enter numbers only.',
    );
    expect(
      controller.session.validationErrors['amount'],
      contains('valid amount'),
    );
    expect(controller.session.validationErrors['date'], 'Choose a valid date.');
    expect(controller.session.validationErrors['time'], 'Choose a valid time.');
    expect(
      controller.session.validationErrors['type'],
      contains('available options'),
    );

    controller.updateManualField('reference', '12');
    controller.updateManualField('amount', '250.00');
    controller.updateManualField('date', '2026-02-28');
    controller.updateManualField('time', '09:30');
    controller.updateManualField('type', 'Savings');
    expect(controller.submitManualDetails(), isTrue);
    expect(controller.session.step, BankingWorkflowStep.review);
    expect(
      controller.populatedDetails
          .firstWhere((detail) => detail.field.id == 'account')
          .displayValue,
      '**** 5678',
    );
  });

  test('session snapshots cannot be used to mutate controller data', () {
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);
    final intent = _allFieldTypesIntent();
    controller.acceptPrediction(intent: intent, confidence: 0.92);
    controller.confirmIntent();
    controller.selectQuery(intent.queries.single);
    controller.continueFromQuerySelection();
    controller.updateManualField('name', 'Private value');

    expect(
      () => controller.session.manualFieldValues['name'] = 'Changed',
      throwsUnsupportedError,
    );
    expect(controller.session.manualFieldValues['name'], 'Private value');
  });
}

BankingIntentConfig _intent(QueryConfiguration configuration, String id) {
  return configuration.intents.firstWhere((intent) => intent.id == id);
}

BankingIntentConfig _allFieldTypesIntent() {
  const fields = <ManualFieldConfig>[
    ManualFieldConfig(
      id: 'name',
      label: 'Name',
      type: ManualFieldType.text,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: 30,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'notes',
      label: 'Notes',
      type: ManualFieldType.multilineText,
      required: false,
      placeholder: null,
      helperText: null,
      maximumLength: 120,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'reference',
      label: 'Reference',
      type: ManualFieldType.number,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: 12,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'account',
      label: 'Account number',
      type: ManualFieldType.maskedNumber,
      required: false,
      placeholder: null,
      helperText: null,
      maximumLength: 20,
      options: <String>[],
      sensitive: true,
      displayMasked: true,
    ),
    ManualFieldConfig(
      id: 'amount',
      label: 'Amount',
      type: ManualFieldType.amount,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: null,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'date',
      label: 'Date',
      type: ManualFieldType.date,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: null,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'time',
      label: 'Time',
      type: ManualFieldType.time,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: null,
      options: <String>[],
      sensitive: false,
      displayMasked: false,
    ),
    ManualFieldConfig(
      id: 'type',
      label: 'Account type',
      type: ManualFieldType.select,
      required: true,
      placeholder: null,
      helperText: null,
      maximumLength: null,
      options: <String>['Current', 'Savings'],
      sensitive: false,
      displayMasked: false,
    ),
  ];
  return const BankingIntentConfig(
    id: 'test_intent',
    displayName: 'Test Intent',
    description: 'Test all local field types.',
    queries: <BankingQueryOption>[
      BankingQueryOption(
        id: 'test_query',
        text: 'I need help with a test request.',
        manualFieldIds: <String>[
          'name',
          'notes',
          'reference',
          'account',
          'amount',
          'date',
          'time',
          'type',
        ],
      ),
    ],
    manualFields: fields,
  );
}
