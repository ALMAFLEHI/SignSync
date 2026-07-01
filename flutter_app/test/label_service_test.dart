import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('loads and validates Sprint 2.13 label metadata assets', () async {
    final metadata = await LabelService().load();

    expect(metadata.labels, hasLength(AppConfig.expectedOutputClasses));
    expect(
      metadata.alphabetModeLabels,
      hasLength(AppConfig.expectedAlphabetModeLabels),
    );
    expect(
      metadata.numberModeLabels,
      hasLength(AppConfig.expectedNumberModeLabels),
    );
    expect(
      metadata.bankingIntentModeLabels,
      hasLength(AppConfig.expectedBankingIntentModeLabels),
    );
  });

  test('filters Alphabet Mode predictions to A-Z only', () async {
    final metadata = await LabelService().load();
    final modeLabels = metadata.labelsForMode(SignMode.alphabet);

    expect(modeLabels, hasLength(26));
    expect(modeLabels, everyElement(matches(RegExp(r'^[A-Z]$'))));
    expect(modeLabels, isNot(contains('7')));
    expect(modeLabels, isNot(contains('deposit')));
  });

  test('filters Number Mode predictions to digits only', () async {
    final metadata = await LabelService().load();
    final modeLabels = metadata.labelsForMode(SignMode.number);

    expect(modeLabels, hasLength(10));
    expect(modeLabels, everyElement(matches(RegExp(r'^[0-9]$'))));
    expect(modeLabels, isNot(contains('A')));
    expect(modeLabels, isNot(contains('deposit')));
  });

  test(
    'filters Banking Intent Mode predictions to banking signs only',
    () async {
      final metadata = await LabelService().load();
      final modeLabels = metadata.labelsForMode(SignMode.bankingIntent);

      expect(modeLabels, hasLength(50));
      expect(modeLabels, containsAll(<String>['deposit', 'transfer', 'atm']));
      expect(modeLabels, isNot(contains('Z')));
      expect(modeLabels, isNot(contains('7')));
    },
  );

  test(
    'Banking Intent Mode excludes high-confidence alphabet outputs',
    () async {
      final metadata = await LabelService().load();
      final probabilities = List<double>.filled(
        AppConfig.expectedOutputClasses,
        0,
      );
      probabilities[metadata.labelMapping['Z']!] = 0.99;
      probabilities[metadata.labelMapping['deposit']!] = 0.75;

      final topLabel = _topLabelForMode(
        metadata: metadata,
        probabilities: probabilities,
        mode: SignMode.bankingIntent,
      );

      expect(topLabel, 'deposit');
    },
  );
}

String _topLabelForMode({
  required LabelMetadata metadata,
  required List<double> probabilities,
  required SignMode mode,
}) {
  final selectedIndices = metadata.indicesForMode(mode);
  final ranked = selectedIndices.toList()
    ..sort(
      (left, right) => probabilities[right].compareTo(probabilities[left]),
    );
  return metadata.labels[ranked.first];
}
