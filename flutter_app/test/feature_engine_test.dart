import 'dart:convert';
import 'dart:io';

import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/services/feature_engine.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('FeatureEngine', () {
    test('returns 756 statistical features for a valid 60x126 sequence', () {
      final frames = List<List<double>>.generate(
        AppConfig.expectedFrameCount,
        (frameIndex) => List<double>.generate(
          AppConfig.expectedFrameWidth,
          (valueIndex) => frameIndex + valueIndex / 1000,
        ),
      );

      final features = FeatureEngine().computeStatisticalFeatures(frames);

      expect(features, hasLength(AppConfig.expectedInputWidth));
    });

    test('rejects an invalid frame count', () {
      final frames = List<List<double>>.generate(
        59,
        (_) => List<double>.filled(AppConfig.expectedFrameWidth, 0),
      );

      expect(
        () => FeatureEngine().computeStatisticalFeatures(frames),
        throwsArgumentError,
      );
    });

    test('rejects an invalid frame width', () {
      final frames = List<List<double>>.generate(
        AppConfig.expectedFrameCount,
        (_) => List<double>.filled(125, 0),
      );

      expect(
        () => FeatureEngine().computeStatisticalFeatures(frames),
        throwsArgumentError,
      );
    });

    test('matches the Sprint 2.16A phone parity fixture', () {
      final fixtureFile = File(
        '../ml/data_phone/fixtures/'
        'P02_PHONE_transfer_R21_feature_parity.json',
      );
      expect(fixtureFile.existsSync(), isTrue);
      final fixture =
          jsonDecode(fixtureFile.readAsStringSync()) as Map<String, dynamic>;
      final frames = (fixture['frames'] as List<dynamic>)
          .map(
            (frame) => (frame as List<dynamic>)
                .map((value) => (value as num).toDouble())
                .toList(growable: false),
          )
          .toList(growable: false);
      final expected = (fixture['expected_features_float32'] as List<dynamic>)
          .map((value) => (value as num).toDouble())
          .toList(growable: false);

      final actual = FeatureEngine().computeStatisticalFeatures(frames);

      expect(actual, hasLength(756));
      expect(expected, hasLength(756));
      for (var index = 0; index < expected.length; index += 1) {
        expect(
          actual[index],
          closeTo(expected[index], 1e-5),
          reason: 'Feature mismatch at index $index',
        );
      }
    });

    test('preserves an all-zero missing left-hand slot', () {
      final frames = List<List<double>>.generate(
        AppConfig.expectedFrameCount,
        (frameIndex) => List<double>.generate(
          AppConfig.expectedFrameWidth,
          (valueIndex) => valueIndex <= 62 ? 0 : frameIndex / 100,
        ),
      );

      final features = FeatureEngine().computeStatisticalFeatures(frames);

      for (var statistic = 0; statistic < 6; statistic += 1) {
        final offset = statistic * AppConfig.expectedFrameWidth;
        expect(
          features.sublist(offset, offset + 63),
          everyElement(0.0),
          reason: 'Left-hand slot changed in statistic block $statistic',
        );
      }
    });
  });
}
