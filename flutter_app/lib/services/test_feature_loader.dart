import 'dart:convert';

import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../models/prediction_result.dart';

class TestFeatureLoader {
  static const List<String> sampleIds = [
    'P02_A_R01',
    'P02_payment_R01',
    'P02_document_R01',
    'P02_signature_R01',
    'P02_atm_R01',
  ];

  Future<TestFeatureSample> load(String sampleId) async {
    if (!sampleIds.contains(sampleId)) {
      throw ArgumentError('Unsupported Sprint 2.14 sample ID: $sampleId');
    }

    final assetPath = '${AppConfig.testFeatureAssetFolder}/$sampleId.json';
    final payload =
        jsonDecode(await rootBundle.loadString(assetPath))
            as Map<String, dynamic>;
    final features = (payload['features'] as List<dynamic>)
        .map((value) => (value as num).toDouble())
        .toList(growable: false);

    if (features.length != AppConfig.expectedInputWidth) {
      throw StateError(
        'Expected 756 features in $assetPath, found ${features.length}.',
      );
    }

    return TestFeatureSample(
      sampleId: payload['sample_id'].toString(),
      trueLabel: payload['true_label'].toString(),
      features: features,
    );
  }
}
