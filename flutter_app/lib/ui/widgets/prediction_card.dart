import 'package:flutter/material.dart';

import '../../models/prediction_result.dart';
import '../../models/sign_mode.dart';

class PredictionCard extends StatelessWidget {
  const PredictionCard({
    super.key,
    required this.sample,
    required this.prediction,
    required this.isPredicting,
  });

  final TestFeatureSample? sample;
  final PredictionResult? prediction;
  final bool isPredicting;

  @override
  Widget build(BuildContext context) {
    final currentSample = sample;
    final currentPrediction = prediction;
    final isCorrect =
        currentSample != null &&
        currentPrediction != null &&
        currentSample.trueLabel == currentPrediction.predictedLabel;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Prediction Result',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            if (isPredicting)
              const LinearProgressIndicator()
            else if (currentSample == null || currentPrediction == null)
              const Text('Choose a test sample to run local inference.')
            else ...[
              _ResultRow(label: 'Sample', value: currentSample.sampleId),
              _ResultRow(label: 'True label', value: currentSample.trueLabel),
              _ResultRow(
                label: 'Predicted label',
                value: currentPrediction.predictedLabel,
              ),
              _ResultRow(
                label: 'Confidence',
                value:
                    '${(currentPrediction.confidence * 100).toStringAsFixed(2)}%',
              ),
              _ResultRow(
                label: 'Mode',
                value: currentPrediction.selectedMode.displayName,
              ),
              _ResultRow(
                label: 'Raw output length',
                value: currentPrediction.rawOutputLength.toString(),
              ),
              const SizedBox(height: 8),
              Chip(
                avatar: Icon(
                  isCorrect ? Icons.check_circle : Icons.cancel,
                  color: isCorrect
                      ? const Color(0xFF047857)
                      : const Color(0xFFB91C1C),
                ),
                label: Text(isCorrect ? 'Correct' : 'Incorrect'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ResultRow extends StatelessWidget {
  const _ResultRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}
