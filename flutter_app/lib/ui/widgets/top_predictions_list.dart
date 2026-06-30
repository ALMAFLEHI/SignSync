import 'package:flutter/material.dart';

import '../../models/prediction_result.dart';

class TopPredictionsList extends StatelessWidget {
  const TopPredictionsList({
    super.key,
    required this.title,
    required this.predictions,
  });

  final String title;
  final List<TopPrediction> predictions;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            for (final prediction in predictions)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    SizedBox(
                      width: 34,
                      child: Text(
                        '#${prediction.index}',
                        style: const TextStyle(color: Color(0xFF64748B)),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        prediction.label,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                    Text(
                      '${(prediction.probability * 100).toStringAsFixed(2)}%',
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
