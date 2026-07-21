import 'package:flutter/material.dart';

class PrivacyStatusChip extends StatelessWidget {
  const PrivacyStatusChip({super.key, required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Chip(
      avatar: Icon(icon, size: 18, color: colors.primary),
      label: Text(label),
      side: BorderSide(color: colors.outlineVariant),
      backgroundColor: colors.surface,
      labelStyle: const TextStyle(fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    );
  }
}
