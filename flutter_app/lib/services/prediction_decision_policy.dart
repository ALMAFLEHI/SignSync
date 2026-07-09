import '../config/app_config.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';

class PredictionDecisionPolicy {
  const PredictionDecisionPolicy();

  static const String tryAgainLabel = 'Try Again';

  PredictionDecision decide({
    required List<TopPrediction> filteredTopPredictions,
    required SignMode mode,
  }) {
    final threshold = confidenceThresholdForMode(mode);
    const minimumGap = AppConfig.minimumTop2Gap;

    if (filteredTopPredictions.isEmpty) {
      return const PredictionDecision(
        accepted: false,
        displayLabel: tryAgainLabel,
        confidenceThreshold: 0,
        minimumTop2Gap: minimumGap,
        top2Gap: 0,
        reason: 'No prediction available for the selected mode.',
      );
    }

    final best = filteredTopPredictions.first;
    final second = filteredTopPredictions.length > 1
        ? filteredTopPredictions[1]
        : null;
    final gap = second == null
        ? best.probability
        : best.probability - second.probability;

    if (best.probability < threshold) {
      return PredictionDecision(
        accepted: false,
        displayLabel: tryAgainLabel,
        confidenceThreshold: threshold,
        minimumTop2Gap: minimumGap,
        top2Gap: gap,
        secondPrediction: second,
        reason:
            'Confidence below ${(threshold * 100).toStringAsFixed(0)}% threshold.',
      );
    }

    if (second != null && gap < minimumGap) {
      return PredictionDecision(
        accepted: false,
        displayLabel: tryAgainLabel,
        confidenceThreshold: threshold,
        minimumTop2Gap: minimumGap,
        top2Gap: gap,
        secondPrediction: second,
        reason:
            'Top predictions are too close; gap is ${(gap * 100).toStringAsFixed(1)}%.',
      );
    }

    return PredictionDecision(
      accepted: true,
      displayLabel: best.label,
      confidenceThreshold: threshold,
      minimumTop2Gap: minimumGap,
      top2Gap: gap,
      secondPrediction: second,
      reason: null,
    );
  }

  double confidenceThresholdForMode(SignMode mode) {
    switch (mode) {
      case SignMode.alphabet:
        return AppConfig.alphabetConfidenceThreshold;
      case SignMode.number:
        return AppConfig.numberConfidenceThreshold;
      case SignMode.bankingIntent:
        return AppConfig.bankingIntentConfidenceThreshold;
    }
  }
}
