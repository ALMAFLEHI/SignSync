import 'package:flutter/material.dart';

import '../../services/test_feature_loader.dart';

class TestSampleButtons extends StatelessWidget {
  const TestSampleButtons({
    super.key,
    required this.enabled,
    required this.onSampleSelected,
  });

  final bool enabled;
  final ValueChanged<String> onSampleSelected;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Test Feature Samples',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: TestFeatureLoader.sampleIds
                  .map((sampleId) {
                    final label = sampleId
                        .replaceFirst('P02_', '')
                        .replaceFirst('_R01', '');
                    return FilledButton.icon(
                      onPressed: enabled
                          ? () => onSampleSelected(sampleId)
                          : null,
                      icon: const Icon(Icons.play_arrow),
                      label: Text('Test $label'),
                    );
                  })
                  .toList(growable: false),
            ),
          ],
        ),
      ),
    );
  }
}
