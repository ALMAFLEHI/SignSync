import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_app/app/signsync_app.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/phone_dataset_collection_page.dart';
import 'package:flutter_app/ui/settings_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('normal home is branded, private, and banking focused', (
    tester,
  ) async {
    await tester.pumpWidget(const SignSyncApp());
    await tester.pumpAndSettle();

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.title, 'SignSync');
    expect(find.text('SignSync'), findsWidgets);
    expect(find.text('Start Banking Interaction'), findsOneWidget);
    expect(find.text('Offline processing'), findsOneWidget);
    expect(find.text('No video upload'), findsOneWidget);
    expect(find.text('Phone Dataset Collection'), findsNothing);
    expect(find.text('Alphabet Mode'), findsNothing);
    expect(find.text('Number Mode'), findsNothing);
    expect(find.text('Final Technical Evaluation'), findsNothing);
  });

  testWidgets('settings exposes developer tools outside the normal home', (
    tester,
  ) async {
    await tester.pumpWidget(const SignSyncApp());
    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();

    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('Developer & Evidence Tools'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Final Model Diagnostics'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Final Model Diagnostics'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Final Technical Evaluation'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Final Technical Evaluation'), findsOneWidget);
    await _showQueryContentPreview(tester);
    expect(find.text('Query Content Preview'), findsOneWidget);
    await _showPhoneSampleCollection(tester);
    expect(find.text('Phone Sample Collection'), findsOneWidget);
  });

  testWidgets('query preview opens from evidence tools', (tester) async {
    await tester.pumpWidget(
      MaterialApp(theme: SignSyncTheme.light, home: const SettingsPage()),
    );
    await _showQueryContentPreview(tester);
    await tester.tap(find.text('Query Content Preview'));
    await tester.pumpAndSettle();

    expect(find.text('Frozen banking query content'), findsOneWidget);
    expect(find.text('Configuration valid'), findsOneWidget);
  });

  testWidgets('collection warning cancel keeps the user in settings', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(theme: SignSyncTheme.light, home: const SettingsPage()),
    );
    await _showPhoneSampleCollection(tester);
    await tester.tap(find.text('Phone Sample Collection'));
    await tester.pumpAndSettle();

    expect(find.text('Evidence Collection Tool'), findsOneWidget);
    expect(
      find.textContaining(
        'not part of the normal SignSync banking interaction',
      ),
      findsOneWidget,
    );
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(find.text('Evidence Collection Tool'), findsNothing);
    expect(find.text('Settings'), findsOneWidget);
  });

  testWidgets('collection warning continue opens the preserved page', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(theme: SignSyncTheme.light, home: const SettingsPage()),
    );
    await _showPhoneSampleCollection(tester);
    await tester.tap(find.text('Phone Sample Collection'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(
      find.text('Sprint 2.16B Full Banking Intent Expansion'),
      findsOneWidget,
    );
    expect(find.byType(PhoneDatasetCollectionPage), findsOneWidget);
  });

  test('visible Android and iOS names changed without package ID changes', () {
    final manifest = File(
      'android/app/src/main/AndroidManifest.xml',
    ).readAsStringSync();
    final gradle = File('android/app/build.gradle.kts').readAsStringSync();
    final iosInfo = File('ios/Runner/Info.plist').readAsStringSync();
    final iosProject = File(
      'ios/Runner.xcodeproj/project.pbxproj',
    ).readAsStringSync();

    expect(manifest, contains('android:label="SignSync"'));
    expect(gradle, contains('applicationId = "com.example.flutter_app"'));
    expect(gradle, contains('namespace = "com.example.flutter_app"'));
    expect(iosInfo, contains('<string>SignSync</string>'));
    expect(
      iosProject,
      contains('PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;'),
    );
  });
}

Future<void> _showPhoneSampleCollection(WidgetTester tester) async {
  await tester.pumpAndSettle();
  await tester.scrollUntilVisible(
    find.text('Phone Sample Collection'),
    250,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
}

Future<void> _showQueryContentPreview(WidgetTester tester) async {
  await tester.pumpAndSettle();
  await tester.scrollUntilVisible(
    find.text('Query Content Preview'),
    250,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
}
