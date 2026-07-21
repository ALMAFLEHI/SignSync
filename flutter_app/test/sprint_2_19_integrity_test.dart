import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'Sprint 2.19 protected Flutter artifacts remain byte-identical',
    () async {
      Future<String> digest(String path) async {
        return (await sha256.bind(File(path).openRead()).first)
            .toString()
            .toUpperCase();
      }

      expect(
        await digest(AppConfig.dynamicRangeModelAsset),
        AppConfig.activeDynamicModelSha256,
      );
      expect(
        await digest(AppConfig.float32ModelAsset),
        'D9686110BACFB1F1C5B3BFBF33B2C515393344869A3DCEAFF325903A34DF278C',
      );
      expect(await digest(AppConfig.labelsAsset), AppConfig.activeLabelsSha256);
      expect(
        await digest(AppConfig.deploymentManifestAsset),
        AppConfig.deploymentManifestSha256,
      );
      expect(AppConfig.bankingIntentConfidenceThreshold, 0.80);
      expect(AppConfig.minimumTop2Gap, 0.00);
    },
  );

  test('package identifiers remain frozen', () {
    final gradle = File('android/app/build.gradle.kts').readAsStringSync();
    final iosProject = File(
      'ios/Runner.xcodeproj/project.pbxproj',
    ).readAsStringSync();
    expect(gradle, contains('applicationId = "${AppConfig.androidPackageId}"'));
    expect(
      iosProject,
      contains('PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;'),
    );
  });
}
