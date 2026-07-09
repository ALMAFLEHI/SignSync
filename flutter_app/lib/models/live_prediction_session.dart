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

class StabilizedPrediction {
  const StabilizedPrediction({
    required this.displayLabel,
    required this.accepted,
    required this.completedCaptures,
    required this.requiredCaptures,
    required this.agreementCount,
    required this.requiredAgreement,
    required this.captureLabels,
  });

  final String displayLabel;
  final bool accepted;
  final int completedCaptures;
  final int requiredCaptures;
  final int agreementCount;
  final int requiredAgreement;
  final List<String?> captureLabels;
}
