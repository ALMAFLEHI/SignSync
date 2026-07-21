import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/query_content_preview_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late QueryConfiguration configuration;

  setUpAll(() {
    final decoded =
        jsonDecode(File(AppConfig.bankingQueriesAsset).readAsStringSync())
            as Map<String, dynamic>;
    configuration = QueryConfiguration.fromJson(
      decoded.cast<String, Object?>(),
    );
    expect(QueryConfigurationValidator.validate(configuration).isValid, isTrue);
  });

  testWidgets('loads and validates the real 40-intent query asset', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: QueryContentPreviewPage(
          service: _StaticQueryConfigurationService(configuration),
        ),
      ),
    );
    await _pumpUntilFound(tester, find.text('Configuration valid'));

    expect(find.text('Query Content Preview'), findsOneWidget);
    expect(find.text('Configuration valid'), findsOneWidget);
    expect(find.text('40 intents | 160 predefined queries'), findsOneWidget);
    expect(find.text('Local read-only content'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('intent-preview-deposit')),
      findsOneWidget,
    );
  });

  testWidgets('filters by intent ID and shows real query details', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: QueryContentPreviewPage(
          service: _StaticQueryConfigurationService(configuration),
        ),
      ),
    );
    await _pumpUntilFound(tester, find.text('Configuration valid'));

    await tester.enterText(
      find.byKey(const ValueKey('query-preview-search')),
      'lost_card',
    );
    await tester.pump();

    final lostCard = find.byKey(const ValueKey('intent-preview-lost_card'));
    expect(lostCard, findsOneWidget);
    expect(find.byKey(const ValueKey('intent-preview-deposit')), findsNothing);

    await tester.tap(lostCard);
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('I lost my debit card.'), findsOneWidget);
    expect(find.text('Please help me block my lost card.'), findsOneWidget);
  });

  testWidgets('dark theme keeps query status, cards, and chips readable', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        darkTheme: SignSyncTheme.dark,
        themeMode: ThemeMode.dark,
        home: QueryContentPreviewPage(
          service: _StaticQueryConfigurationService(configuration),
        ),
      ),
    );
    await _pumpUntilFound(tester, find.text('Configuration valid'));

    final summary = find.byKey(const ValueKey('query-validation-summary'));
    final colors = Theme.of(tester.element(summary)).colorScheme;
    final summaryContainer = tester.widget<Container>(summary);
    final summaryDecoration = summaryContainer.decoration! as BoxDecoration;
    final summaryTitle = tester.widget<Text>(find.text('Configuration valid'));
    expect(summaryDecoration.color, colors.primaryContainer);
    expect(summaryTitle.style?.color, colors.onPrimaryContainer);
    expect(find.text('40 intents | 160 predefined queries'), findsOneWidget);
    expect(find.text('Local read-only content'), findsOneWidget);

    final search = find.byKey(const ValueKey('query-preview-search'));
    expect(
      Theme.of(tester.element(search)).inputDecorationTheme.fillColor,
      colors.surfaceContainerHigh,
    );

    final deposit = find.byKey(const ValueKey('intent-preview-deposit'));
    final depositCard = tester.widget<Card>(deposit);
    expect(depositCard.color, colors.surfaceContainerLow);

    await tester.tap(deposit);
    await tester.pump(const Duration(milliseconds: 350));

    final description = tester.widget<Text>(
      find.text(
        'Requests related to depositing cash or cheques into an account.',
      ),
    );
    final chipFinder = find.byKey(
      const ValueKey('manual-field-chip-deposit-amount'),
    );
    final chip = tester.widget<Chip>(chipFinder);
    expect(description.style?.color, colors.onSurfaceVariant);
    expect(chip.backgroundColor, colors.surfaceContainerHigh);
    expect(chip.labelStyle?.color, colors.onSurface);
  });
}

Future<void> _pumpUntilFound(WidgetTester tester, Finder finder) async {
  for (var attempt = 0; attempt < 100; attempt += 1) {
    await tester.pump(const Duration(milliseconds: 100));
    if (finder.evaluate().isNotEmpty) {
      return;
    }
  }
  fail('Timed out waiting for the expected query preview widget.');
}

class _StaticQueryConfigurationService extends QueryConfigurationService {
  _StaticQueryConfigurationService(this.configuration);

  final QueryConfiguration configuration;

  @override
  Future<QueryConfiguration> load() async => configuration;
}
