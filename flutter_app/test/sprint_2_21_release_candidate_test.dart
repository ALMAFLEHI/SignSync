import 'dart:convert';
import 'dart:io';

import 'package:flutter_app/app/signsync_app.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('release starts on the normal private banking home', (
    tester,
  ) async {
    await tester.pumpWidget(const SignSyncApp());
    await tester.pumpAndSettle();

    expect(find.text('Start Banking Interaction'), findsOneWidget);
    expect(find.text('Offline processing'), findsOneWidget);
    expect(find.text('Developer & Evidence Tools'), findsNothing);
    expect(find.text('Phone Sample Collection'), findsNothing);
    expect(find.text('Final Model Diagnostics'), findsNothing);
  });

  test('frozen release identity and inference contract remain exact', () {
    expect(BankingIntentScope.frozenIntents, hasLength(40));
    expect(BankingIntentScope.frozenIntents[4], 'account');
    expect(BankingIntentScope.frozenIntents[13], 'savings');
    expect(AppConfig.expectedFrameCount, 60);
    expect(AppConfig.expectedFrameWidth, 126);
    expect(AppConfig.expectedInputWidth, 756);
    expect(AppConfig.expectedOutputClasses, 40);
    expect(AppConfig.bankingIntentConfidenceThreshold, 0.80);
    expect(AppConfig.minimumTop2Gap, 0.00);
    expect(AppConfig.androidPackageId, 'com.example.flutter_app');
    expect(AppConfig.iosBundleId, 'com.example.flutterApp');
  });

  test('all 40 intents retain exactly four local requests', () {
    final configuration =
        jsonDecode(File(AppConfig.bankingQueriesAsset).readAsStringSync())
            as Map<String, dynamic>;
    final intents = configuration['intents'] as List<dynamic>;

    expect(
      intents.map((intent) => (intent as Map<String, dynamic>)['id']).toList(),
      BankingIntentScope.frozenIntents,
    );
    expect(
      intents.every(
        (intent) =>
            ((intent as Map<String, dynamic>)['queries'] as List<dynamic>)
                .length ==
            4,
      ),
      isTrue,
    );
  });

  test('protected deployed model assets are included in source releases', () {
    final gitignore = File('../.gitignore').readAsStringSync();
    for (final asset in [
      AppConfig.dynamicRangeModelAsset,
      AppConfig.float32ModelAsset,
    ]) {
      expect(File(asset).existsSync(), isTrue, reason: asset);
      expect(gitignore, contains('!flutter_app/$asset'), reason: asset);
    }
  });

  test(
    'Android release permission policy keeps camera and removes unused access',
    () {
      final manifest = File(
        'android/app/src/main/AndroidManifest.xml',
      ).readAsStringSync();
      expect(manifest, contains('android.permission.CAMERA'));
      for (final permission in [
        'INTERNET',
        'ACCESS_NETWORK_STATE',
        'READ_EXTERNAL_STORAGE',
        'WRITE_EXTERNAL_STORAGE',
        'READ_PHONE_STATE',
      ]) {
        expect(
          manifest,
          contains(
            'android:name="android.permission.$permission" tools:node="remove"',
          ),
          reason: permission,
        );
      }
      expect(
        File('android/app/src/debug/AndroidManifest.xml').readAsStringSync(),
        contains('android.permission.INTERNET'),
      );
      expect(
        manifest,
        contains(
          'android:name="android.permission.INTERNET" tools:node="remove"',
        ),
      );
    },
  );

  test('version and application identifiers remain unchanged', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    final gradle = File('android/app/build.gradle.kts').readAsStringSync();
    final ios = File('ios/Runner.xcodeproj/project.pbxproj').readAsStringSync();

    expect(pubspec, contains('version: 1.0.0+1'));
    expect(gradle, contains('applicationId = "com.example.flutter_app"'));
    expect(
      ios,
      contains('PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;'),
    );
  });
}
