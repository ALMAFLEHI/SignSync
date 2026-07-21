import '../config/banking_intent_scope.dart';
import '../config/app_config.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';

class BankingPredictionEvaluation {
  const BankingPredictionEvaluation({
    required this.accepted,
    required this.intentId,
    required this.message,
  });

  final bool accepted;
  final String? intentId;
  final String message;
}

class BankingPredictionGate {
  const BankingPredictionGate();

  BankingPredictionEvaluation evaluate(PredictionResult prediction) {
    if (prediction.selectedMode != SignMode.bankingIntent) {
      return const BankingPredictionEvaluation(
        accepted: false,
        intentId: null,
        message: 'This result is not a supported banking intent.',
      );
    }
    if (prediction.rawOutputLength != AppConfig.expectedOutputClasses ||
        !prediction.confidence.isFinite) {
      return const BankingPredictionEvaluation(
        accepted: false,
        intentId: null,
        message: 'The local model configuration is invalid.',
      );
    }
    final label = prediction.predictedLabel;
    if (!BankingIntentScope.frozenIntents.contains(label)) {
      return const BankingPredictionEvaluation(
        accepted: false,
        intentId: null,
        message: 'This result is not a supported banking intent.',
      );
    }
    if (!prediction.decision.accepted ||
        prediction.confidence < prediction.decision.confidenceThreshold) {
      return const BankingPredictionEvaluation(
        accepted: false,
        intentId: null,
        message: 'The sign could not be recognized confidently.',
      );
    }
    if (prediction.decision.displayLabel != label) {
      return const BankingPredictionEvaluation(
        accepted: false,
        intentId: null,
        message: 'The sign could not be recognized confidently.',
      );
    }
    return BankingPredictionEvaluation(
      accepted: true,
      intentId: label,
      message: 'Banking intent recognized.',
    );
  }
}
