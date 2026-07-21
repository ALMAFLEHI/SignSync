import 'dart:convert';
import 'dart:io';

import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('deployed metadata matches the frozen 40-class scope', () async {
    final metadata = await LabelService().load();
    final contract = metadata.modelMetadata['contract'] as Map<String, dynamic>;

    expect(contract['input_shape'], <int>[1, 756]);
    expect(contract['output_shape'], <int>[1, 40]);
    expect(contract['input_dtype'], 'float32');
    expect(contract['output_dtype'], 'float32');
    expect(metadata.labels, hasLength(40));
    expect(metadata.labels, orderedEquals(BankingIntentScope.frozenIntents));
    expect(metadata.labelMapping, <String, int>{
      for (final entry in metadata.labels.indexed) entry.$2: entry.$1,
    });
  });

  test('feature metadata preserves the canonical Flutter contract', () async {
    final metadata = await LabelService().load();
    final contract = metadata.featureContract;
    final standardDeviation =
        contract['standard_deviation'] as Map<String, dynamic>;

    expect(contract['sequence_shape'], <int>[60, 126]);
    expect(contract['model_input_shape'], <int>[1, 756]);
    expect(contract['dtype'], 'float32');
    expect(standardDeviation['ddof'], 0);
    expect(contract['statistic_order'], <String>[
      'mean',
      'population_std',
      'minimum',
      'maximum',
      'first_frame',
      'last_frame',
    ]);
  });

  test('corrected Sprint 2.17 parity set agrees for both variants', () {
    final verificationFile = File(
      '../ml/models/sprint_2_17_final_40class_account_corrected_v2/metadata/'
      'tflite_verification.json',
    );
    final parityFile = File(
      '../ml/models/sprint_2_17_final_40class_account_corrected_v2/metrics/'
      'tflite_parity.csv',
    );
    expect(verificationFile.existsSync(), isTrue);
    expect(parityFile.existsSync(), isTrue);

    final verification =
        jsonDecode(verificationFile.readAsStringSync()) as Map<String, dynamic>;
    final parityLines = parityFile
        .readAsLinesSync()
        .where((line) => line.trim().isNotEmpty)
        .toList(growable: false);

    expect(verification['parity_samples'], 40);
    expect(verification['keras_float32_top1_agreement'], 1.0);
    expect(verification['keras_dynamic_top1_agreement'], 1.0);
    expect(parityLines, hasLength(41));
    for (final row in parityLines.skip(1)) {
      final values = row.split(',');
      expect(values[7], 'True');
      expect(values[8], 'True');
    }
  });

  test('active asset paths use only the versioned 40-class models', () {
    expect(
      AppConfig.dynamicRangeModelAsset,
      'assets/models/'
      'signsync_40class_account_corrected_v2_dynamic_range.tflite',
    );
    expect(
      AppConfig.float32ModelAsset,
      'assets/models/'
      'signsync_40class_account_corrected_v2_float32.tflite',
    );
    expect(AppConfig.labelsAsset, 'assets/models/labels_40.json');
    expect(AppConfig.expectedOutputClasses, 40);
    expect(AppConfig.bankingOnlyRecognition, isTrue);
  });
}
