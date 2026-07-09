import '../config/app_config.dart';
import '../models/live_prediction_session.dart';
import '../models/prediction_result.dart';
import 'prediction_decision_policy.dart';

class StabilizedPredictionTracker {
  StabilizedPredictionTracker({
    this.requiredCaptures = AppConfig.stabilizedCaptureCount,
    this.requiredAgreement = AppConfig.stabilizedAgreementCount,
  });

  final int requiredCaptures;
  final int requiredAgreement;
  final List<String?> _acceptedLabels = <String?>[];

  StabilizedPrediction get current {
    return _buildState();
  }

  StabilizedPrediction add(PredictionResult prediction) {
    if (_acceptedLabels.length >= requiredCaptures) {
      reset();
    }
    _acceptedLabels.add(
      prediction.decision.accepted ? prediction.decision.displayLabel : null,
    );
    return _buildState();
  }

  void reset() {
    _acceptedLabels.clear();
  }

  StabilizedPrediction _buildState() {
    final counts = <String, int>{};
    for (final label in _acceptedLabels.whereType<String>()) {
      counts[label] = (counts[label] ?? 0) + 1;
    }

    String? majorityLabel;
    var agreementCount = 0;
    for (final entry in counts.entries) {
      if (entry.value > agreementCount) {
        majorityLabel = entry.key;
        agreementCount = entry.value;
      }
    }

    final complete = _acceptedLabels.length >= requiredCaptures;
    final accepted = complete && agreementCount >= requiredAgreement;

    return StabilizedPrediction(
      displayLabel: accepted
          ? majorityLabel!
          : (complete
                ? PredictionDecisionPolicy.tryAgainLabel
                : 'Waiting for $requiredCaptures captures'),
      accepted: accepted,
      completedCaptures: _acceptedLabels.length,
      requiredCaptures: requiredCaptures,
      agreementCount: agreementCount,
      requiredAgreement: requiredAgreement,
      captureLabels: List<String?>.unmodifiable(_acceptedLabels),
    );
  }
}
