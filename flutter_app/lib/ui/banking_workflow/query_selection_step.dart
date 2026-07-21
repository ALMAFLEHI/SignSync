import 'package:flutter/material.dart';

import '../../models/banking_interaction_session.dart';
import '../../models/query_configuration.dart';
import '../../theme/signsync_theme.dart';

class QuerySelectionStep extends StatelessWidget {
  const QuerySelectionStep({
    super.key,
    required this.session,
    required this.onSelected,
    required this.onContinue,
    required this.onBack,
    required this.onCancel,
  });

  final BankingInteractionSession session;
  final ValueChanged<BankingQueryOption> onSelected;
  final VoidCallback onContinue;
  final VoidCallback onBack;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    final intent = session.detectedIntent!;
    final selectedQuery = session.selectedQuery;
    return ListView(
      key: const ValueKey('query-selection-step'),
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        Text(
          'Select your exact request',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        Text('Confirmed topic: ${intent.displayName}'),
        const SizedBox(height: 16),
        for (final query in intent.queries) ...[
          _QueryOption(
            query: query,
            selected: selectedQuery?.id == query.id,
            onTap: () => onSelected(query),
          ),
          const SizedBox(height: 8),
        ],
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const ValueKey('query-continue'),
          onPressed: selectedQuery == null ? null : onContinue,
          icon: const Icon(Icons.arrow_forward),
          label: const Text('Continue'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: onBack,
          icon: const Icon(Icons.arrow_back),
          label: const Text('Back'),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: onCancel,
          child: const Text('Cancel Interaction'),
        ),
      ],
    );
  }
}

class _QueryOption extends StatelessWidget {
  const _QueryOption({
    required this.query,
    required this.selected,
    required this.onTap,
  });

  final BankingQueryOption query;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final background = selected
        ? colors.primaryContainer
        : colors.surfaceContainerHigh;
    final foreground = selected ? colors.onPrimaryContainer : colors.onSurface;
    return Semantics(
      selected: selected,
      button: true,
      child: Material(
        key: ValueKey('query-option-${query.id}'),
        color: background,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(SignSyncTheme.radius),
          side: BorderSide(
            color: selected ? colors.primary : colors.outlineVariant,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(SignSyncTheme.radius),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  selected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_unchecked,
                  color: selected ? colors.onPrimaryContainer : colors.primary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(query.text, style: TextStyle(color: foreground)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
