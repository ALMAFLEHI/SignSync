import 'dart:convert';
import 'dart:io';

import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'deployed Experiment B metadata matches the 76-class V3 scope',
    () async {
      final metadata = await LabelService().load();
      final scopeFile = File('../ml/config/signsync_active_scope_v3_40.json');
      expect(scopeFile.existsSync(), isTrue);
      final scope =
          jsonDecode(scopeFile.readAsStringSync()) as Map<String, dynamic>;
      final activeBanking = (scope['active_banking_intents'] as List<dynamic>)
          .map((value) => value.toString())
          .toList(growable: false);
      final removed = (scope['removed_banking_intents'] as List<dynamic>)
          .map((value) => value.toString())
          .toList(growable: false);

      expect(metadata.modelMetadata['input_shape'], <int>[1, 756]);
      expect(metadata.modelMetadata['output_shape'], <int>[1, 76]);
      expect(metadata.labels, hasLength(76));
      expect(metadata.allLabels, orderedEquals(metadata.labels));
      expect(metadata.alphabetModeLabels, hasLength(26));
      expect(metadata.numberModeLabels, hasLength(10));
      expect(metadata.bankingIntentModeLabels, hasLength(40));
      expect(metadata.bankingIntentModeLabels, orderedEquals(activeBanking));
      expect(metadata.removedBankingIntents, orderedEquals(removed));
      for (final label in removed) {
        expect(metadata.labels, isNot(contains(label)));
      }
      expect(metadata.labelMapping, <String, int>{
        for (final entry in metadata.labels.indexed) entry.$2: entry.$1,
      });
    },
  );

  test(
    'preprocessing metadata preserves the Flutter feature contract',
    () async {
      final metadata = await LabelService().load();
      final config = metadata.preprocessingConfig;

      expect(config['source_sequence_shape'], <int>[60, 126]);
      expect(config['feature_width'], AppConfig.expectedInputWidth);
      expect(config['standard_deviation_ddof'], 0);
      expect(config['left_hand_indices'], <int>[0, 62]);
      expect(config['right_hand_indices'], <int>[63, 125]);
      expect(config['feature_order'], <String>[
        'mean',
        'std',
        'min',
        'max',
        'first_frame',
        'last_frame',
      ]);
    },
  );

  test('verified Experiment B deterministic predictions are preserved', () {
    final fixtureFile = File(
      'test/fixtures/experiment_b_tflite_predictions.json',
    );
    expect(fixtureFile.existsSync(), isTrue);
    final fixture =
        jsonDecode(fixtureFile.readAsStringSync()) as Map<String, dynamic>;
    final predictions = fixture['predictions'] as List<dynamic>;

    expect(fixture['input_shape'], <int>[1, 756]);
    expect(fixture['output_shape'], <int>[1, 76]);
    expect(predictions, hasLength(4));
    for (final predictionValue in predictions) {
      final prediction = predictionValue as Map<String, dynamic>;
      expect(prediction['dynamic_top1'], prediction['expected_label']);
      expect(prediction['float_top1'], prediction['expected_label']);
    }
  });
}
