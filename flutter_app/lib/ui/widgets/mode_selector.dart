import 'package:flutter/material.dart';

import '../../models/sign_mode.dart';

class ModeSelector extends StatelessWidget {
  const ModeSelector({
    super.key,
    required this.selectedMode,
    required this.onChanged,
  });

  final SignMode selectedMode;
  final ValueChanged<SignMode> onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recognition Mode',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            SegmentedButton<SignMode>(
              segments: SignMode.values
                  .map((mode) {
                    return ButtonSegment<SignMode>(
                      value: mode,
                      icon: Icon(
                        mode == SignMode.normal
                            ? Icons.sign_language
                            : Icons.pin,
                      ),
                      label: Text(mode.displayName),
                    );
                  })
                  .toList(growable: false),
              selected: {selectedMode},
              onSelectionChanged: (selection) => onChanged(selection.first),
            ),
            const SizedBox(height: 8),
            Text(
              selectedMode.description,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: const Color(0xFF64748B)),
            ),
          ],
        ),
      ),
    );
  }
}
