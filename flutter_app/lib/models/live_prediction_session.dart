import 'prediction_result.dart';

class LiveCaptureMetrics {
  const LiveCaptureMetrics({
    required this.validFrameCount,
    required this.frameDimension,
    required this.captureDurationMs,
    required this.averageFps,
  });

  final int validFrameCount;
  final int frameDimension;
  final int captureDurationMs;
  final double averageFps;
}

class LivePredictionSession {
  const LivePredictionSession({
    required this.prediction,
    required this.featureLength,
    required this.captureMetrics,
    required this.featureComputationMs,
    required this.inferenceMs,
    required this.endToEndMs,
  });

  final PredictionResult prediction;
  final int featureLength;
  final LiveCaptureMetrics captureMetrics;
  final int featureComputationMs;
  final int inferenceMs;
  final int endToEndMs;
}
