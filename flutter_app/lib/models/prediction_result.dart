import 'sign_mode.dart';

class TopPrediction {
  const TopPrediction({
    required this.label,
    required this.probability,
    required this.index,
  });

  final String label;
  final double probability;
  final int index;
}

class PredictionResult {
  const PredictionResult({
    required this.predictedLabel,
    required this.confidence,
    required this.decision,
    required this.topPredictions,
    required this.rawTopPredictions,
    required this.rawOutputLength,
    required this.selectedMode,
    required this.modelAsset,
  });

  final String predictedLabel;
  final double confidence;
  final PredictionDecision decision;
  final List<TopPrediction> topPredictions;
  final List<TopPrediction> rawTopPredictions;
  final int rawOutputLength;
  final SignMode selectedMode;
  final String modelAsset;
}

class PredictionDecision {
  const PredictionDecision({
    required this.accepted,
    required this.displayLabel,
    required this.confidenceThreshold,
    required this.minimumTop2Gap,
    required this.top2Gap,
    required this.reason,
    this.secondPrediction,
  });

  final bool accepted;
  final String displayLabel;
  final double confidenceThreshold;
  final double minimumTop2Gap;
  final double top2Gap;
  final String? reason;
  final TopPrediction? secondPrediction;
}

class TestFeatureSample {
  const TestFeatureSample({
    required this.sampleId,
    required this.trueLabel,
    required this.features,
  });

  final String sampleId;
  final String trueLabel;
  final List<double> features;
}
