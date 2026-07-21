import 'package:flutter/material.dart';

import '../../models/banking_interaction_session.dart';
import '../../theme/signsync_theme.dart';

class IntentConfirmationStep extends StatelessWidget {
  const IntentConfirmationStep({
    super.key,
    required this.session,
    required this.onConfirm,
    required this.onTryAgain,
    required this.onCancel,
  });

  final BankingInteractionSession session;
  final VoidCallback onConfirm;
  final VoidCallback onTryAgain;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    final intent = session.detectedIntent!;
    final confidence = session.confidence!;
    final colors = Theme.of(context).colorScheme;
    return ListView(
      key: const ValueKey('intent-confirmation-step'),
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        Text(
          'Confirm the banking topic',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 8),
        const Text('Is this the banking topic you intended?'),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: colors.primaryContainer,
            borderRadius: BorderRadius.circular(SignSyncTheme.radius),
            border: Border.all(color: colors.primary),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Detected intent',
                style: TextStyle(color: colors.onPrimaryContainer),
              ),
              const SizedBox(height: 6),
              Text(
                intent.displayName,
                key: const ValueKey('detected-intent-name'),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: colors.onPrimaryContainer,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Confidence: ${(confidence * 100).toStringAsFixed(0)}%',
                style: TextStyle(color: colors.onPrimaryContainer),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          key: const ValueKey('confirm-intent'),
          onPressed: onConfirm,
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('Confirm Intent'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const ValueKey('confirmation-try-again'),
          onPressed: onTryAgain,
          icon: const Icon(Icons.refresh),
          label: const Text('Try Again'),
        ),
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: onCancel,
          icon: const Icon(Icons.close),
          label: const Text('Cancel Interaction'),
        ),
      ],
    );
  }
}
