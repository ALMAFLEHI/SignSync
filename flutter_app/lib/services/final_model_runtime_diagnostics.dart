class FinalModelRuntimeDiagnostics {
  FinalModelRuntimeDiagnostics._();

  static double? modelLoadMs;
  static double? featureComputationMs;
  static double? inferenceMs;
  static double? predictionProcessingMs;

  static void recordModelLoad(Duration duration) {
    modelLoadMs = duration.inMicroseconds / 1000;
  }

  static void recordPrediction({
    required Duration featureDuration,
    required Duration inferenceDuration,
    required Duration processingDuration,
  }) {
    featureComputationMs = featureDuration.inMicroseconds / 1000;
    inferenceMs = inferenceDuration.inMicroseconds / 1000;
    predictionProcessingMs = processingDuration.inMicroseconds / 1000;
  }

  static void clearPredictionTimings() {
    featureComputationMs = null;
    inferenceMs = null;
    predictionProcessingMs = null;
  }
}
