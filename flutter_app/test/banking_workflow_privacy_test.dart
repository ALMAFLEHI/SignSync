import 'dart:io';

import 'package:flutter_app/controllers/banking_interaction_controller.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('manual interaction values are not written to preferences', () async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final configuration = await QueryConfigurationService().load();
    final transfer = configuration.intents.firstWhere(
      (intent) => intent.id == 'transfer',
    );
    final controller = BankingInteractionController();
    addTearDown(controller.dispose);

    controller.acceptPrediction(intent: transfer, confidence: 0.94);
    controller.confirmIntent();
    controller.selectQuery(
      transfer.queries.firstWhere((query) => query.id == 'transfer_money'),
    );
    controller.continueFromQuerySelection();
    controller.updateManualField('amount', '250.00');
    controller.updateManualField('beneficiary_account', '12345678');

    final preferences = await SharedPreferences.getInstance();
    expect(preferences.getKeys(), isEmpty);
  });

  test(
    'workflow source contains no logging, file writing, or preference access',
    () {
      final source = <String>[
        'lib/controllers/banking_interaction_controller.dart',
        'lib/models/banking_interaction_session.dart',
        'lib/ui/banking_interaction_page.dart',
        'lib/ui/banking_workflow/manual_details_step.dart',
        'lib/ui/banking_workflow/request_review_step.dart',
        'lib/ui/banking_workflow/banker_request_view.dart',
      ].map((path) => File(path).readAsStringSync()).join('\n');

      for (final forbidden in <String>[
        'SharedPreferences',
        'print(',
        'debugPrint(',
        'developer.log(',
        'File(',
        'writeAsString',
        'writeAsBytes',
        'http.',
        'https://',
      ]) {
        expect(source, isNot(contains(forbidden)), reason: forbidden);
      }
    },
  );

  test('query configuration remains a read-only bundled JSON asset', () {
    final service = File(
      'lib/services/query_configuration_service.dart',
    ).readAsStringSync();
    final pubspec = File('pubspec.yaml').readAsStringSync();

    expect(File('assets/content/banking_queries.json').existsSync(), isTrue);
    expect(pubspec, contains('assets/content/banking_queries.json'));
    expect(service, contains('loadString'));
    expect(service, isNot(contains('writeAs')));
    expect(service, isNot(contains('SharedPreferences')));
  });
}
