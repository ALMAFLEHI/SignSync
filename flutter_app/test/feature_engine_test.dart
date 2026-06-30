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
  });
}
