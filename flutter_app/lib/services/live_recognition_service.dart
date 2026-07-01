import '../config/app_config.dart';
import '../models/live_prediction_session.dart';
import '../models/sign_mode.dart';
import 'feature_engine.dart';
import 'tflite_sign_classifier.dart';

class LiveRecognitionService {
  LiveRecognitionService({
    required TfliteSignClassifier classifier,
    FeatureEngine? featureEngine,
  }) : _classifier = classifier,
       _featureEngine = featureEngine ?? FeatureEngine();

  final TfliteSignClassifier _classifier;
  final FeatureEngine _featureEngine;

  LivePredictionSession predictFromFrames({
    required List<List<double>> frames,
    required SignMode mode,
    required LiveCaptureMetrics captureMetrics,
  }) {
    final endToEndWatch = Stopwatch()..start();

    final featureWatch = Stopwatch()..start();
    final features = _featureEngine.computeStatisticalFeatures(frames);
    featureWatch.stop();

    if (features.length != AppConfig.expectedInputWidth) {
      throw StateError(
        'Expected ${AppConfig.expectedInputWidth} live features, found ${features.length}.',
      );
    }

    final inferenceWatch = Stopwatch()..start();
    final prediction = _classifier.predict(features, mode);
    inferenceWatch.stop();
    endToEndWatch.stop();

    return LivePredictionSession(
      prediction: prediction,
      featureLength: features.length,
      captureMetrics: captureMetrics,
      featureComputationMs: featureWatch.elapsedMilliseconds,
      inferenceMs: inferenceWatch.elapsedMilliseconds,
      endToEndMs: endToEndWatch.elapsedMilliseconds,
    );
  }
}
