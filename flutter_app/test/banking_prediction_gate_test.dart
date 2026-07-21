import 'package:flutter_app/models/prediction_result.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/services/banking_prediction_gate.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const gate = BankingPredictionGate();

  test('accepts a confident frozen banking intent', () {
    final result = gate.evaluate(_prediction('transfer'));

    expect(result.accepted, isTrue);
    expect(result.intentId, 'transfer');
  });

  for (final unsupportedLabel in <String>['A', '7', 'address_change']) {
    test('rejects unsupported result $unsupportedLabel without remapping', () {
      final result = gate.evaluate(_prediction(unsupportedLabel));

      expect(result.accepted, isFalse);
      expect(result.intentId, isNull);
      expect(result.message, 'This result is not a supported banking intent.');
    });
  }

  test('rejects a low-confidence banking result', () {
    final result = gate.evaluate(
      _prediction('deposit', confidence: 0.42, accepted: false),
    );

    expect(result.accepted, isFalse);
    expect(result.intentId, isNull);
    expect(result.message, 'The sign could not be recognized confidently.');
  });

  test('rejects results produced outside banking mode', () {
    final result = gate.evaluate(
      _prediction('deposit', mode: SignMode.alphabet),
    );

    expect(result.accepted, isFalse);
    expect(result.intentId, isNull);
  });

  test('rejects an invalid final-model output length', () {
    final result = gate.evaluate(_prediction('deposit', rawOutputLength: 76));

    expect(result.accepted, isFalse);
    expect(result.message, 'The local model configuration is invalid.');
  });

  test('rejects a non-finite final-model confidence', () {
    final result = gate.evaluate(
      _prediction('deposit', confidence: double.nan),
    );

    expect(result.accepted, isFalse);
    expect(result.message, 'The local model configuration is invalid.');
  });
}

PredictionResult _prediction(
  String label, {
  double confidence = 0.95,
  bool accepted = true,
  SignMode mode = SignMode.bankingIntent,
  int rawOutputLength = 40,
}) {
  final top = TopPrediction(label: label, probability: confidence, index: 0);
  return PredictionResult(
    predictedLabel: label,
    confidence: confidence,
    decision: PredictionDecision(
      accepted: accepted,
      displayLabel: accepted ? label : '',
      confidenceThreshold: 0.90,
      minimumTop2Gap: 0.00,
      top2Gap: 0.50,
      reason: accepted ? null : 'Below confidence threshold.',
    ),
    topPredictions: <TopPrediction>[top],
    rawTopPredictions: <TopPrediction>[top],
    rawOutputLength: rawOutputLength,
    selectedMode: mode,
    modelAsset: 'unchanged-test-model.tflite',
  );
}
