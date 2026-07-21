import 'dart:async';

import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../theme/signsync_theme.dart';
import '../theme/app_theme_preference.dart';
import '../theme/theme_controller.dart';
import 'final_model_diagnostics_page.dart';
import 'final_technical_evaluation_page.dart';
import 'live_camera_page.dart';
import 'phone_dataset_collection_page.dart';
import 'query_content_preview_page.dart';
import 'widgets/evidence_tool_tile.dart';
import 'widgets/section_header.dart';
import 'widgets/signsync_logo.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  Future<void> _openCollectionTool(BuildContext context) async {
    final shouldContinue = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Evidence Collection Tool'),
        content: const Text(
          'This page is retained for project dataset evidence and controlled '
          'sample collection. It is not part of the normal SignSync banking '
          'interaction workflow.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Continue'),
          ),
        ],
      ),
    );
    if (shouldContinue != true || !context.mounted) {
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const PhoneDatasetCollectionPage(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeController = ThemeControllerScope.maybeOf(context);
    final selectedTheme =
        themeController?.preference ?? AppThemePreference.system;
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
          children: [
            const SignSyncWordmark(markSize: 44),
            const SizedBox(height: 8),
            Text(
              'Private, on-device banking communication assistance.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            const SectionHeader(
              title: 'Appearance',
              description: 'Choose how SignSync looks on this device.',
            ),
            const SizedBox(height: 12),
            SegmentedButton<AppThemePreference>(
              key: const ValueKey('theme-selector'),
              segments: const <ButtonSegment<AppThemePreference>>[
                ButtonSegment<AppThemePreference>(
                  value: AppThemePreference.system,
                  icon: Icon(Icons.settings_suggest_outlined),
                  label: Text('System'),
                ),
                ButtonSegment<AppThemePreference>(
                  value: AppThemePreference.light,
                  icon: Icon(Icons.light_mode_outlined),
                  label: Text('Light'),
                ),
                ButtonSegment<AppThemePreference>(
                  value: AppThemePreference.dark,
                  icon: Icon(Icons.dark_mode_outlined),
                  label: Text('Dark'),
                ),
              ],
              selected: <AppThemePreference>{selectedTheme},
              onSelectionChanged: themeController == null
                  ? null
                  : (selection) {
                      unawaited(
                        themeController.setPreference(selection.single),
                      );
                    },
            ),
            const SizedBox(height: 24),
            const SectionHeader(title: 'Privacy & app information'),
            const SizedBox(height: 8),
            const ListTile(
              contentPadding: EdgeInsets.symmetric(horizontal: 4),
              leading: Icon(Icons.offline_bolt_outlined),
              title: Text('Offline processing'),
              subtitle: Text('Recognition and content remain on this device.'),
            ),
            const ListTile(
              contentPadding: EdgeInsets.symmetric(horizontal: 4),
              leading: Icon(Icons.info_outline),
              title: Text('About SignSync'),
              subtitle: Text(
                '${AppConfig.appTitle} supports privacy-preserving banking '
                'communication and does not connect to bank systems.',
              ),
            ),
            const Divider(height: 32),
            const SectionHeader(
              title: 'Developer & Evidence Tools',
              description:
                  'Project review utilities kept outside the normal user flow.',
            ),
            const SizedBox(height: 4),
            EvidenceToolTile(
              icon: Icons.verified_outlined,
              title: 'Final Model Diagnostics',
              subtitle:
                  'Verify the deployed 40-class model, labels, hashes, and contract.',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const FinalModelDiagnosticsPage(),
                  ),
                );
              },
            ),
            EvidenceToolTile(
              icon: Icons.developer_mode_outlined,
              title: 'Final Model Live Diagnostics',
              subtitle:
                  'Run banking-only camera and timing checks for controlled evidence.',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const LiveCameraPage(bankingOnly: true),
                  ),
                );
              },
            ),
            EvidenceToolTile(
              icon: Icons.science_outlined,
              title: 'Final Technical Evaluation',
              subtitle:
                  'Run the frozen 400-trial Samsung A55 research protocol.',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const FinalTechnicalEvaluationPage(),
                  ),
                );
              },
            ),
            EvidenceToolTile(
              icon: Icons.fact_check_outlined,
              title: 'Query Content Preview',
              subtitle:
                  'Review and validate all 40 local intent configurations.',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const QueryContentPreviewPage(),
                  ),
                );
              },
            ),
            EvidenceToolTile(
              icon: Icons.dataset_outlined,
              title: 'Phone Sample Collection',
              subtitle:
                  'Open the preserved controlled dataset collection tool.',
              onTap: () => _openCollectionTool(context),
            ),
          ],
        ),
      ),
    );
  }
}
