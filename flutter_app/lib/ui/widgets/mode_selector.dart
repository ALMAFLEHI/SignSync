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
            const SizedBox(height: 6),
            Text(
              'Use Alphabet Mode for letters, Number Mode for digits, and Banking Intent Mode for banking signs.',
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: const Color(0xFF475569)),
            ),
            const SizedBox(height: 12),
            for (final mode in SignMode.values) ...[
              _ModeOption(
                mode: mode,
                icon: _iconForMode(mode),
                isSelected: selectedMode == mode,
                onTap: () => onChanged(mode),
              ),
              if (mode != SignMode.values.last) const SizedBox(height: 8),
            ],
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

  IconData _iconForMode(SignMode mode) {
    switch (mode) {
      case SignMode.alphabet:
        return Icons.abc;
      case SignMode.number:
        return Icons.pin;
      case SignMode.bankingIntent:
        return Icons.account_balance;
    }
  }
}

class _ModeOption extends StatelessWidget {
  const _ModeOption({
    required this.mode,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  final SignMode mode;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final borderColor = isSelected
        ? colorScheme.primary
        : const Color(0xFFE2E8F0);
    final backgroundColor = isSelected
        ? colorScheme.primary.withValues(alpha: 0.08)
        : Colors.white;

    return Material(
      color: backgroundColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: borderColor, width: isSelected ? 1.5 : 1),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              Icon(icon, color: isSelected ? colorScheme.primary : null),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      mode.displayName,
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: isSelected ? colorScheme.primary : null,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      mode.description,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF64748B),
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                isSelected
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
                color: isSelected
                    ? colorScheme.primary
                    : const Color(0xFF94A3B8),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
