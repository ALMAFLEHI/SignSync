import 'package:flutter_app/models/prediction_result.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/prediction_decision_policy.dart';
import 'package:flutter_app/services/stabilized_prediction_tracker.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PredictionDecisionPolicy', () {
    const policy = PredictionDecisionPolicy();

    test('accepts confident banking intent predictions with enough gap', () {
      final decision = policy.decide(
        mode: SignMode.bankingIntent,
        filteredTopPredictions: const [
          TopPrediction(label: 'deposit', probability: 0.91, index: 36),
          TopPrediction(label: 'transfer', probability: 0.42, index: 39),
        ],
      );

      expect(decision.accepted, isTrue);
      expect(decision.displayLabel, 'deposit');
    });

    test('returns Try Again when confidence is below mode threshold', () {
      final decision = policy.decide(
        mode: SignMode.bankingIntent,
        filteredTopPredictions: const [
          TopPrediction(label: 'transfer', probability: 0.66, index: 39),
          TopPrediction(label: 'deposit', probability: 0.25, index: 36),
        ],
      );

      expect(decision.accepted, isFalse);
      expect(decision.displayLabel, PredictionDecisionPolicy.tryAgainLabel);
      expect(decision.reason, contains('Confidence below'));
    });

    test('returns Try Again when top-2 predictions are too close', () {
      final decision = policy.decide(
        mode: SignMode.number,
        filteredTopPredictions: const [
          TopPrediction(label: '7', probability: 0.70, index: 33),
          TopPrediction(label: '1', probability: 0.61, index: 27),
        ],
      );

      expect(decision.accepted, isFalse);
      expect(decision.displayLabel, PredictionDecisionPolicy.tryAgainLabel);
      expect(decision.reason, contains('too close'));
    });

    test('returns Try Again for low-confidence document/card ambiguity', () {
      final decision = policy.decide(
        mode: SignMode.bankingIntent,
        filteredTopPredictions: const [
          TopPrediction(label: 'card', probability: 0.605791, index: 41),
          TopPrediction(label: 'document', probability: 0.350086, index: 57),
        ],
      );

      expect(decision.accepted, isFalse);
      expect(decision.displayLabel, PredictionDecisionPolicy.tryAgainLabel);
      expect(decision.confidenceThreshold, 0.70);
      expect(decision.minimumTop2Gap, 0.15);
      expect(decision.reason, contains('Confidence below'));
    });
  });

  group('StabilizedPredictionTracker', () {
    test('accepts a label when 2 out of 3 captures agree', () {
      final tracker = StabilizedPredictionTracker();

      tracker.add(_prediction('transfer', accepted: true));
      tracker.add(_prediction('transfer', accepted: true));
      final stabilized = tracker.add(_prediction('deposit', accepted: true));

      expect(stabilized.accepted, isTrue);
      expect(stabilized.displayLabel, 'transfer');
      expect(stabilized.agreementCount, 2);
    });

    test('returns Try Again when 3 captures do not agree', () {
      final tracker = StabilizedPredictionTracker();

      tracker.add(_prediction('transfer', accepted: true));
      tracker.add(_prediction('deposit', accepted: true));
      final stabilized = tracker.add(_prediction('balance', accepted: true));

      expect(stabilized.accepted, isFalse);
      expect(stabilized.displayLabel, PredictionDecisionPolicy.tryAgainLabel);
    });
  });
}

PredictionResult _prediction(String label, {required bool accepted}) {
  final top = TopPrediction(label: label, probability: 0.9, index: 0);
  return PredictionResult(
    predictedLabel: label,
    confidence: top.probability,
    decision: PredictionDecision(
      accepted: accepted,
      displayLabel: accepted ? label : PredictionDecisionPolicy.tryAgainLabel,
      confidenceThreshold: 0.70,
      minimumTop2Gap: 0.15,
      top2Gap: 0.4,
      reason: accepted ? null : 'test rejection',
    ),
    topPredictions: [top],
    rawTopPredictions: [top],
    rawOutputLength: 76,
    selectedMode: SignMode.bankingIntent,
    modelAsset: 'test.tflite',
  );
}
