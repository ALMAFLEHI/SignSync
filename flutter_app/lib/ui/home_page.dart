import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../theme/signsync_theme.dart';
import 'banking_interaction_page.dart';
import 'settings_page.dart';
import 'widgets/privacy_status_chip.dart';
import 'widgets/section_header.dart';
import 'widgets/signsync_logo.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  void _openLiveBankingInteraction(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => const BankingInteractionPage()),
    );
  }

  void _openSettings(BuildContext context) {
    Navigator.of(
      context,
    ).push(MaterialPageRoute<void>(builder: (_) => const SettingsPage()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const SignSyncWordmark(markSize: 34),
        actions: [
          IconButton(
            tooltip: 'Settings',
            onPressed: () => _openSettings(context),
            icon: const Icon(
              Icons.settings_outlined,
              semanticLabel: 'Open SignSync settings',
            ),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
          children: [
            _BrandIntroduction(
              onStart: () => _openLiveBankingInteraction(context),
            ),
            const SizedBox(height: 28),
            const SectionHeader(
              title: 'How it works',
              description:
                  'A guided path from a banking sign to a clear request.',
            ),
            const SizedBox(height: 12),
            const _HowItWorks(),
            const SizedBox(height: 28),
            const _PrivacyNotice(),
          ],
        ),
      ),
    );
  }
}

class _BrandIntroduction extends StatelessWidget {
  const _BrandIntroduction({required this.onStart});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SignSyncLogo(size: 64),
          const SizedBox(height: 16),
          Text(
            AppConfig.appTitle,
            style: Theme.of(
              context,
            ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(
            'Private, on-device banking communication assistance.',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: colors.onSurfaceVariant,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 16),
          const Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              PrivacyStatusChip(
                icon: Icons.offline_bolt_outlined,
                label: 'Offline processing',
              ),
              PrivacyStatusChip(
                icon: Icons.videocam_off_outlined,
                label: 'No video upload',
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              key: const ValueKey('start-banking-interaction'),
              onPressed: onStart,
              icon: const Icon(Icons.sign_language_outlined),
              label: const Text('Start Banking Interaction'),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Recognizes banking intents only. Exact names, amounts, dates, and '
            'account details will be entered manually.',
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

class _HowItWorks extends StatelessWidget {
  const _HowItWorks();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        _StepRow(
          number: 1,
          icon: Icons.sign_language_outlined,
          title: 'Perform a banking sign',
          description: 'Use the camera to communicate one banking intent.',
        ),
        _StepRow(
          number: 2,
          icon: Icons.verified_outlined,
          title: 'Confirm the detected intent',
          description: 'Review the banking intent before continuing.',
        ),
        _StepRow(
          number: 3,
          icon: Icons.list_alt_outlined,
          title: 'Select the exact request',
          description: 'Choose a predefined request and add optional details.',
        ),
        _StepRow(
          number: 4,
          icon: Icons.co_present_outlined,
          title: 'Show the request to the banker',
          description: 'Present clear text for an in-branch conversation.',
          showDivider: false,
        ),
      ],
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({
    required this.number,
    required this.icon,
    required this.title,
    required this.description,
    this.showDivider = true,
  });

  final int number;
  final IconData icon;
  final String title;
  final String description;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: colors.primaryContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: colors.onPrimaryContainer),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$number. $title',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      description,
                      style: TextStyle(color: colors.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1),
      ],
    );
  }
}

class _PrivacyNotice extends StatelessWidget {
  const _PrivacyNotice();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(SignSyncTheme.radius),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.lock_outline,
            color: Theme.of(context).colorScheme.onSecondaryContainer,
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Recognition runs on this device. Camera frames are not uploaded. '
              'SignSync does not connect to bank systems or execute transactions.',
            ),
          ),
        ],
      ),
    );
  }
}
