import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_app/services/phone_sample_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('loads and validates the final 40-class deployment metadata', () async {
    final metadata = await LabelService().load();

    expect(metadata.labels, hasLength(AppConfig.expectedOutputClasses));
    expect(metadata.labels, orderedEquals(BankingIntentScope.frozenIntents));
    expect(metadata.alphabetModeLabels, isEmpty);
    expect(metadata.numberModeLabels, isEmpty);
    expect(metadata.bankingIntentModeLabels, hasLength(40));
    expect(metadata.removedBankingIntents, hasLength(10));
    expect(metadata.queryIntentIds, orderedEquals(metadata.labels));
    expect(metadata.queryCount, 160);
    expect(metadata.queryMappingMatches, isTrue);
  });

  test('rejects historical Alphabet Mode for the final model', () async {
    final metadata = await LabelService().load();

    expect(
      () => metadata.labelsForMode(SignMode.alphabet),
      throwsUnsupportedError,
    );
  });

  test('rejects historical Number Mode for the final model', () async {
    final metadata = await LabelService().load();

    expect(
      () => metadata.labelsForMode(SignMode.number),
      throwsUnsupportedError,
    );
  });

  test('Banking Intent Mode uses the exact frozen output order', () async {
    final metadata = await LabelService().load();
    final modeLabels = metadata.labelsForMode(SignMode.bankingIntent);

    expect(modeLabels, hasLength(40));
    expect(modeLabels, orderedEquals(BankingIntentScope.frozenIntents));
    expect(modeLabels, everyElement(isNot(matches(RegExp(r'^[A-Z0-9]$')))));
  });

  test('final model metadata excludes removed and historical labels', () async {
    final metadata = await LabelService().load();

    for (final label in BankingIntentScope.removedIntents) {
      expect(metadata.labels, isNot(contains(label)));
      expect(metadata.labelMapping, isNot(contains(label)));
    }
    expect(metadata.labelMapping, isNot(contains('Z')));
    expect(metadata.labelMapping, isNot(contains('7')));
  });

  test('deployment and confidence metadata match the active runtime', () async {
    final metadata = await LabelService().load();

    expect(metadata.deploymentManifest['input_shape'], <int>[1, 756]);
    expect(metadata.deploymentManifest['output_shape'], <int>[1, 40]);
    expect(metadata.deploymentManifest['label_count'], 40);
    expect(
      metadata.deploymentManifest['confidence_threshold'],
      AppConfig.bankingIntentConfidenceThreshold,
    );
    expect(metadata.deploymentManifest['minimum_margin'], 0.0);
    expect(
      metadata.deploymentManifest['default_model_asset'],
      AppConfig.dynamicRangeModelAsset,
    );
  });

  test('phone pilot offers only four retained weak labels', () {
    expect(
      PhoneSampleStore.weakLabels,
      orderedEquals(<String>['transfer', 'document', 'signature', 'atm']),
    );
    expect(PhoneSampleStore.weakLabels, isNot(contains('address_change')));
    expect(
      PhoneSampleStore.weakLabels.length *
          PhoneSampleStore.sprint216ATargetSamplesPerLabel,
      100,
    );
  });
}
