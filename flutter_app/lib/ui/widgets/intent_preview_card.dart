import 'package:flutter/material.dart';

import '../../models/query_configuration.dart';

class IntentPreviewCard extends StatelessWidget {
  const IntentPreviewCard({super.key, required this.intent});

  final BankingIntentConfig intent;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      key: ValueKey('intent-preview-${intent.id}'),
      color: colorScheme.surfaceContainerLow,
      clipBehavior: Clip.antiAlias,
      child: ExpansionTile(
        backgroundColor: colorScheme.surfaceContainerLow,
        collapsedBackgroundColor: colorScheme.surfaceContainerLow,
        textColor: colorScheme.onSurface,
        collapsedTextColor: colorScheme.onSurface,
        iconColor: colorScheme.primary,
        collapsedIconColor: colorScheme.onSurfaceVariant,
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        title: Text(
          intent.displayName,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(intent.id),
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              intent.description,
              style: TextStyle(color: colorScheme.onSurfaceVariant),
            ),
          ),
          const SizedBox(height: 12),
          for (var index = 0; index < intent.queries.length; index += 1) ...[
            _QueryRow(index: index + 1, query: intent.queries[index]),
            if (index != intent.queries.length - 1) const Divider(height: 20),
          ],
          if (intent.manualFields.isNotEmpty) ...[
            const Divider(height: 24),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Optional manual fields',
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final field in intent.manualFields)
                    Chip(
                      key: ValueKey(
                        'manual-field-chip-${intent.id}-${field.id}',
                      ),
                      backgroundColor: colorScheme.surfaceContainerHigh,
                      side: BorderSide(color: colorScheme.outlineVariant),
                      labelStyle: TextStyle(color: colorScheme.onSurface),
                      label: Text('${field.label} | ${field.type.id}'),
                      avatar: Icon(
                        field.sensitive
                            ? Icons.visibility_off
                            : Icons.edit_note,
                        size: 17,
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _QueryRow extends StatelessWidget {
  const _QueryRow({required this.index, required this.query});

  final int index;
  final BankingQueryOption query;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 28,
          child: Text(
            '$index.',
            style: TextStyle(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(query.text),
              if (query.manualFieldIds.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  'Fields: ${query.manualFieldIds.join(', ')}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
