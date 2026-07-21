import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../config/banking_intent_scope.dart';
import '../models/sign_mode.dart';

class LabelMetadata {
  const LabelMetadata({
    required this.labels,
    required this.labelMapping,
    required this.removedBankingIntents,
    required this.modelMetadata,
    required this.featureContract,
    required this.confidenceRecommendation,
    required this.deploymentManifest,
    required this.queryIntentIds,
    required this.queryCount,
  });

  final List<String> labels;
  final Map<String, int> labelMapping;
  final List<String> removedBankingIntents;
  final Map<String, Object?> modelMetadata;
  final Map<String, Object?> featureContract;
  final Map<String, Object?> confidenceRecommendation;
  final Map<String, Object?> deploymentManifest;
  final List<String> queryIntentIds;
  final int queryCount;

  List<String> get allLabels => labels;
  List<String> get alphabetModeLabels => const <String>[];
  List<String> get numberModeLabels => const <String>[];
  List<String> get bankingIntentModeLabels => labels;
  bool get queryMappingMatches => _sameOrder(labels, queryIntentIds);

  List<String> labelsForMode(SignMode mode) {
    if (!mode.isActiveForFinalModel) {
      throw UnsupportedError(
        'Historical recognition mode is unavailable with the final 40-class model.',
      );
    }
    return bankingIntentModeLabels;
  }

  List<int> indicesForMode(SignMode mode) {
    return indicesForLabels(labelsForMode(mode));
  }

  List<int> indicesForLabels(Iterable<String> selectedLabels) {
    return selectedLabels
        .map((label) {
          final index = labelMapping[label];
          if (index == null) {
            throw StateError('Label "$label" is missing from final metadata.');
          }
          return index;
        })
        .toList(growable: false);
  }
}

class LabelService {
  LabelService({AssetBundle? assetBundle})
    : _assetBundle = assetBundle ?? rootBundle;

  final AssetBundle _assetBundle;

  Future<LabelMetadata> load() async {
    try {
      final labels = _readJsonStringList(
        await _assetBundle.loadString(AppConfig.labelsAsset),
        'labels',
      );
      final modelMetadata = _readJsonObject(
        await _assetBundle.loadString(AppConfig.modelMetadataAsset),
        'model metadata',
      );
      final featureContract = _readJsonObject(
        await _assetBundle.loadString(AppConfig.featureContractAsset),
        'feature contract',
      );
      final confidenceRecommendation = _readJsonObject(
        await _assetBundle.loadString(AppConfig.confidenceRecommendationAsset),
        'confidence recommendation',
      );
      final deploymentManifest = _readJsonObject(
        await _assetBundle.loadString(AppConfig.deploymentManifestAsset),
        'deployment manifest',
      );
      final queryData = _readJsonObject(
        await _assetBundle.loadString(AppConfig.bankingQueriesAsset),
        'query configuration',
      );
      final queryIntents = _readObjectList(queryData, 'intents');
      final queryIntentIds = queryIntents
          .map((intent) => intent['id'].toString())
          .toList(growable: false);
      final queryCount = queryIntents.fold<int>(
        0,
        (total, intent) => total + _readList(intent, 'queries').length,
      );

      final metadata = LabelMetadata(
        labels: labels,
        labelMapping: <String, int>{
          for (final entry in labels.indexed) entry.$2: entry.$1,
        },
        removedBankingIntents: BankingIntentScope.removedIntents,
        modelMetadata: modelMetadata,
        featureContract: featureContract,
        confidenceRecommendation: confidenceRecommendation,
        deploymentManifest: deploymentManifest,
        queryIntentIds: queryIntentIds,
        queryCount: queryCount,
      );
      validate(metadata);
      return metadata;
    } catch (error, stackTrace) {
      developer.log(
        'Final model metadata loading failed',
        error: error,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  void validate(LabelMetadata metadata) {
    BankingIntentScope.validate();
    if (metadata.labels.length != AppConfig.expectedOutputClasses ||
        metadata.labels.toSet().length != AppConfig.expectedOutputClasses) {
      throw StateError('The final model requires exactly 40 unique labels.');
    }
    if (!_sameOrder(metadata.labels, BankingIntentScope.frozenIntents)) {
      throw StateError('Final model labels do not match the frozen order.');
    }
    if (!_sameOrder(metadata.queryIntentIds, metadata.labels) ||
        metadata.queryCount != 160) {
      throw StateError(
        'Query configuration must match all 40 model labels in exact order.',
      );
    }
    if (metadata.labels.any((label) => RegExp(r'^[A-Z0-9]$').hasMatch(label)) ||
        metadata.labels.any(BankingIntentScope.removedIntents.contains)) {
      throw StateError(
        'Alphabet, digit, and removed labels cannot enter the final model.',
      );
    }
    if (metadata.labelMapping.length != metadata.labels.length ||
        metadata.labels.indexed.any(
          (entry) => metadata.labelMapping[entry.$2] != entry.$1,
        )) {
      throw StateError('The final label-to-index mapping is inconsistent.');
    }

    final manifest = metadata.deploymentManifest;
    _requireShape(manifest, 'input_shape', const <int>[1, 756]);
    _requireShape(manifest, 'output_shape', const <int>[1, 40]);
    if (manifest['input_dtype'] != 'float32' ||
        manifest['output_dtype'] != 'float32' ||
        manifest['label_count'] != AppConfig.expectedOutputClasses ||
        manifest['confidence_threshold'] !=
            AppConfig.bankingIntentConfidenceThreshold ||
        manifest['minimum_margin'] != AppConfig.minimumTop2Gap ||
        manifest['default_model_asset'] != AppConfig.dynamicRangeModelAsset ||
        manifest['fallback_model_asset'] != AppConfig.float32ModelAsset ||
        manifest['labels_asset'] != AppConfig.labelsAsset ||
        manifest['deployment_status'] != AppConfig.deploymentStatus ||
        manifest['model_version'] != AppConfig.modelVersion) {
      throw StateError(
        'Deployment manifest does not match active runtime config.',
      );
    }

    final modelContract = _readObject(metadata.modelMetadata, 'contract');
    _requireShape(modelContract, 'input_shape', const <int>[1, 756]);
    _requireShape(modelContract, 'output_shape', const <int>[1, 40]);
    final packagedLabels = _readStringList(
      metadata.modelMetadata,
      'label_order',
    );
    if (metadata.modelMetadata['label_count'] != 40 ||
        !_sameOrder(packagedLabels, metadata.labels) ||
        modelContract['input_dtype'] != 'float32' ||
        modelContract['output_dtype'] != 'float32') {
      throw StateError('Packaged model metadata does not match deployment.');
    }

    _requireShape(metadata.featureContract, 'sequence_shape', const <int>[
      60,
      126,
    ]);
    _requireShape(metadata.featureContract, 'model_input_shape', const <int>[
      1,
      756,
    ]);
    if (!_sameOrder(
          _readStringList(metadata.featureContract, 'statistic_order'),
          const <String>[
            'mean',
            'population_std',
            'minimum',
            'maximum',
            'first_frame',
            'last_frame',
          ],
        ) ||
        _readObject(metadata.featureContract, 'standard_deviation')['ddof'] !=
            0 ||
        metadata.featureContract['dtype'] != 'float32') {
      throw StateError(
        'Feature contract does not match Flutter preprocessing.',
      );
    }
    if (metadata.confidenceRecommendation['minimum_confidence'] !=
            AppConfig.bankingIntentConfidenceThreshold ||
        metadata.confidenceRecommendation['minimum_top2_margin'] !=
            AppConfig.minimumTop2Gap ||
        metadata.confidenceRecommendation['selected_using'] !=
            'phone validation only') {
      throw StateError(
        'Confidence policy differs from the frozen recommendation.',
      );
    }
  }

  Map<String, Object?> _readJsonObject(String raw, String name) {
    final value = jsonDecode(raw);
    if (value is! Map<String, Object?>) {
      throw FormatException('$name must be a JSON object.');
    }
    return value;
  }

  List<String> _readJsonStringList(String raw, String name) {
    final value = jsonDecode(raw);
    if (value is! List<Object?> || value.any((item) => item is! String)) {
      throw FormatException('$name must be a JSON string list.');
    }
    return value.cast<String>().toList(growable: false);
  }

  void _requireShape(
    Map<String, Object?> source,
    String key,
    List<int> expected,
  ) {
    final actual = _readIntList(source, key);
    if (!_sameOrder(actual, expected)) {
      throw StateError('$key must be $expected, found $actual.');
    }
  }
}

Map<String, Object?> _readObject(Map<String, Object?> data, String key) {
  final value = data[key];
  if (value is! Map<String, Object?>) {
    throw StateError('$key is missing or is not an object.');
  }
  return value;
}

List<Object?> _readList(Map<String, Object?> data, String key) {
  final value = data[key];
  if (value is! List<Object?>) {
    throw StateError('$key is missing or is not a list.');
  }
  return value;
}

List<Map<String, Object?>> _readObjectList(
  Map<String, Object?> data,
  String key,
) {
  return _readList(data, key)
      .map((value) {
        if (value is! Map<String, Object?>) {
          throw StateError('$key must contain objects.');
        }
        return value;
      })
      .toList(growable: false);
}

List<int> _readIntList(Map<String, Object?> data, String key) {
  return _readList(
    data,
    key,
  ).map((value) => (value as num).toInt()).toList(growable: false);
}

List<String> _readStringList(Map<String, Object?> data, String key) {
  return _readList(
    data,
    key,
  ).map((value) => value.toString()).toList(growable: false);
}

bool _sameOrder<T>(List<T> left, List<T> right) {
  if (left.length != right.length) {
    return false;
  }
  for (var index = 0; index < left.length; index += 1) {
    if (left[index] != right[index]) {
      return false;
    }
  }
  return true;
}
