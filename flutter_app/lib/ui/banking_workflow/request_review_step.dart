import 'package:flutter/material.dart';

import '../../controllers/banking_interaction_controller.dart';
import '../../models/banking_interaction_session.dart';
import '../../theme/signsync_theme.dart';

class RequestReviewStep extends StatelessWidget {
  const RequestReviewStep({
    super.key,
    required this.controller,
    required this.session,
    required this.onShowToBanker,
    required this.onEditRequest,
    required this.onEditDetails,
    required this.onStartOver,
  });

  final BankingInteractionController controller;
  final BankingInteractionSession session;
  final VoidCallback onShowToBanker;
  final VoidCallback onEditRequest;
  final VoidCallback onEditDetails;
  final VoidCallback onStartOver;

  @override
  Widget build(BuildContext context) {
    final intent = session.detectedIntent!;
    final query = session.selectedQuery!;
    final details = controller.populatedDetails;
    return ListView(
      key: const ValueKey('request-review-step'),
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        Text(
          'Review your request',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 16),
        _ReviewSection(label: 'Banking topic', value: intent.displayName),
        const SizedBox(height: 12),
        _ReviewSection(label: 'Selected request', value: query.text),
        for (final detail in details) ...[
          const SizedBox(height: 12),
          _ReviewSection(
            key: ValueKey('review-detail-${detail.field.id}'),
            label: detail.field.label,
            value: detail.displayValue,
          ),
        ],
        const SizedBox(height: 20),
        FilledButton.icon(
          key: const ValueKey('show-to-banker'),
          onPressed: onShowToBanker,
          icon: const Icon(Icons.co_present_outlined),
          label: const Text('Show to Banker'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: onEditRequest,
          icon: const Icon(Icons.edit_outlined),
          label: const Text('Edit Request'),
        ),
        if (controller.selectedManualFields.isNotEmpty) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: onEditDetails,
            icon: const Icon(Icons.edit_note_outlined),
            label: const Text('Edit Details'),
          ),
        ],
        const SizedBox(height: 8),
        TextButton.icon(
          key: const ValueKey('review-start-over'),
          onPressed: onStartOver,
          icon: const Icon(Icons.restart_alt),
          label: const Text('Start Over'),
        ),
      ],
    );
  }
}

class _ReviewSection extends StatelessWidget {
  const _ReviewSection({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(SignSyncTheme.radius),
        border: Border.all(color: colors.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: colors.onSurfaceVariant)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
