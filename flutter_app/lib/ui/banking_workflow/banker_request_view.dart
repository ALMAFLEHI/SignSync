import 'package:flutter/material.dart';

import '../../controllers/banking_interaction_controller.dart';
import '../../models/banking_interaction_session.dart';
import '../../theme/signsync_theme.dart';
import '../widgets/privacy_status_chip.dart';
import '../widgets/signsync_logo.dart';

class BankerRequestView extends StatelessWidget {
  const BankerRequestView({
    super.key,
    required this.controller,
    required this.session,
    required this.onBackToReview,
    required this.onNewInteraction,
    required this.onClearSession,
  });

  final BankingInteractionController controller;
  final BankingInteractionSession session;
  final VoidCallback onBackToReview;
  final VoidCallback onNewInteraction;
  final VoidCallback onClearSession;

  @override
  Widget build(BuildContext context) {
    final intent = session.detectedIntent!;
    final query = session.selectedQuery!;
    final details = controller.populatedDetails;
    final colors = Theme.of(context).colorScheme;
    return ListView(
      key: const ValueKey('banker-request-view'),
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        const SignSyncWordmark(markSize: 42),
        const SizedBox(height: 24),
        Text(
          'Customer Banking Request',
          style: Theme.of(
            context,
          ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 20),
        Text(
          'Banking topic',
          style: TextStyle(color: colors.onSurfaceVariant, fontSize: 16),
        ),
        const SizedBox(height: 4),
        Text(
          intent.displayName,
          key: const ValueKey('banker-topic'),
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const Divider(height: 32),
        Text(
          'Customer request',
          style: TextStyle(color: colors.onSurfaceVariant, fontSize: 16),
        ),
        const SizedBox(height: 6),
        Text(
          query.text,
          key: const ValueKey('banker-request-text'),
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            height: 1.35,
          ),
        ),
        for (final detail in details) ...[
          const Divider(height: 32),
          Text(
            detail.field.label,
            style: TextStyle(color: colors.onSurfaceVariant, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            detail.displayValue,
            key: ValueKey('banker-detail-${detail.field.id}'),
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
          ),
        ],
        const SizedBox(height: 24),
        const Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            PrivacyStatusChip(
              icon: Icons.offline_bolt_outlined,
              label: 'Offline processing',
            ),
            PrivacyStatusChip(icon: Icons.lock_outline, label: 'Session only'),
          ],
        ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: colors.secondaryContainer,
            borderRadius: BorderRadius.circular(SignSyncTheme.radius),
          ),
          child: Text(
            'SignSync communicates the customer\'s request. Banking actions must '
            'be completed by authorized bank staff.',
            style: TextStyle(color: colors.onSecondaryContainer),
          ),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          key: const ValueKey('banker-new-interaction'),
          onPressed: onNewInteraction,
          icon: const Icon(Icons.add_comment_outlined),
          label: const Text('New Interaction'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: onBackToReview,
          icon: const Icon(Icons.arrow_back),
          label: const Text('Back to Review'),
        ),
        const SizedBox(height: 8),
        TextButton.icon(
          key: const ValueKey('banker-clear-session'),
          onPressed: onClearSession,
          icon: const Icon(Icons.delete_outline),
          label: const Text('Clear Session'),
        ),
      ],
    );
  }
}
