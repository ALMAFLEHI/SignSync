import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../models/sign_mode.dart';

class LabelMetadata {
  const LabelMetadata({
    required this.labels,
    required this.labelMapping,
    required this.allLabels,
    required this.alphabetModeLabels,
    required this.numberModeLabels,
    required this.bankingIntentModeLabels,
    required this.removedBankingIntents,
    required this.modelMetadata,
    required this.preprocessingConfig,
  });

  final List<String> labels;
  final Map<String, int> labelMapping;
  final List<String> allLabels;
  final List<String> alphabetModeLabels;
  final List<String> numberModeLabels;
  final List<String> bankingIntentModeLabels;
  final List<String> removedBankingIntents;
  final Map<String, Object?> modelMetadata;
  final Map<String, Object?> preprocessingConfig;

  List<String> labelsForMode(SignMode mode) {
    switch (mode) {
      case SignMode.alphabet:
        return alphabetModeLabels;
      case SignMode.number:
        return numberModeLabels;
      case SignMode.bankingIntent:
        return bankingIntentModeLabels;
    }
  }

  List<int> indicesForMode(SignMode mode) {
    return indicesForLabels(labelsForMode(mode));
  }

  List<int> indicesForLabels(Iterable<String> selectedLabels) {
    return selectedLabels
        .map((label) {
          final index = labelMapping[label];
          if (index == null) {
            throw StateError(
              'Label "$label" is missing from label_mapping.json.',
            );
          }
          return index;
        })
        .toList(growable: false);
  }
}

class LabelService {
  Future<LabelMetadata> load() async {
    try {
      final labelsText = await rootBundle.loadString(AppConfig.labelsAsset);
      final mappingText = await rootBundle.loadString(
        AppConfig.labelMappingAsset,
      );
      final groupsText = await rootBundle.loadString(
        AppConfig.labelGroupsAsset,
      );
      final metadataText = await rootBundle.loadString(
        AppConfig.modelMetadataAsset,
      );
      final preprocessingText = await rootBundle.loadString(
        AppConfig.preprocessingConfigAsset,
      );

      final labels = labelsText
          .split(RegExp(r'\r?\n'))
          .where((label) => label.trim().isNotEmpty)
          .map((label) => label.trim())
          .toList(growable: false);
      final labelMapping = (jsonDecode(mappingText) as Map<String, dynamic>)
          .map((key, value) => MapEntry(key, (value as num).toInt()));
      final groups = jsonDecode(groupsText) as Map<String, dynamic>;
      final modelMetadata = (jsonDecode(metadataText) as Map<String, dynamic>)
          .cast<String, Object?>();
      final preprocessingConfig =
          (jsonDecode(preprocessingText) as Map<String, dynamic>)
              .cast<String, Object?>();

      final metadata = LabelMetadata(
        labels: labels,
        labelMapping: labelMapping,
        allLabels: _readStringList(groups, 'all_labels'),
        alphabetModeLabels: _readStringList(groups, 'alphabet_mode'),
        numberModeLabels: _readStringList(groups, 'number_mode'),
        bankingIntentModeLabels: _readStringList(groups, 'banking_intent_mode'),
        removedBankingIntents: _readStringList(
          groups,
          'removed_banking_intents',
        ),
        modelMetadata: modelMetadata,
        preprocessingConfig: preprocessingConfig,
      );
      validate(metadata);
      return metadata;
    } catch (error, stackTrace) {
      developer.log(
        'Label metadata loading failed',
        error: error,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  void validate(LabelMetadata metadata) {
    final inputShape = (metadata.modelMetadata['input_shape'] as List<dynamic>)
        .map((value) => (value as num).toInt())
        .toList();
    final outputShape =
        (metadata.modelMetadata['output_shape'] as List<dynamic>)
            .map((value) => (value as num).toInt())
            .toList();

    if (metadata.labels.length != AppConfig.expectedOutputClasses) {
      throw StateError(
        'Expected ${AppConfig.expectedOutputClasses} labels, '
        'found ${metadata.labels.length}.',
      );
    }
    if (metadata.allLabels.length != AppConfig.expectedOutputClasses) {
      throw StateError(
        'Expected ${AppConfig.expectedOutputClasses} all_labels entries, '
        'found ${metadata.allLabels.length}.',
      );
    }
    if (metadata.alphabetModeLabels.length !=
        AppConfig.expectedAlphabetModeLabels) {
      throw StateError(
        'Expected 26 alphabet mode labels, found ${metadata.alphabetModeLabels.length}.',
      );
    }
    if (metadata.numberModeLabels.length !=
        AppConfig.expectedNumberModeLabels) {
      throw StateError(
        'Expected 10 number mode labels, found ${metadata.numberModeLabels.length}.',
      );
    }
    if (metadata.bankingIntentModeLabels.length !=
        AppConfig.expectedBankingIntentModeLabels) {
      throw StateError(
        'Expected 40 banking intent mode labels, found ${metadata.bankingIntentModeLabels.length}.',
      );
    }
    if (metadata.removedBankingIntents.length !=
        AppConfig.expectedRemovedBankingIntents) {
      throw StateError(
        'Expected 10 removed banking intents, found ${metadata.removedBankingIntents.length}.',
      );
    }
    if (metadata.labels.toSet().length != metadata.labels.length) {
      throw StateError('Model labels must be unique.');
    }
    if (!_sameOrder(metadata.labels, metadata.allLabels)) {
      throw StateError('labels.txt and all_labels must use the same order.');
    }
    final groupedLabels = <String>[
      ...metadata.alphabetModeLabels,
      ...metadata.numberModeLabels,
      ...metadata.bankingIntentModeLabels,
    ];
    if (!_sameOrder(metadata.labels, groupedLabels)) {
      throw StateError(
        'Alphabet, number, and banking mode groups must match model order.',
      );
    }
    if (metadata.labelMapping.length != metadata.labels.length ||
        metadata.labels.indexed.any(
          (entry) => metadata.labelMapping[entry.$2] != entry.$1,
        )) {
      throw StateError('label_mapping.json must match labels.txt order.');
    }
    if (metadata.removedBankingIntents.any(
      (label) =>
          metadata.labels.contains(label) ||
          metadata.labelMapping.containsKey(label) ||
          metadata.bankingIntentModeLabels.contains(label),
    )) {
      throw StateError(
        'Removed banking intents cannot appear in deployed model metadata.',
      );
    }
    if (metadata.bankingIntentModeLabels.any(
      (label) => !metadata.labels.contains(label),
    )) {
      throw StateError(
        'Every active banking intent must remain mapped by the historical model.',
      );
    }
    if (inputShape.length != 2 ||
        inputShape[0] != 1 ||
        inputShape[1] != AppConfig.expectedInputWidth) {
      throw StateError(
        'Expected model input shape [1, 756], found $inputShape.',
      );
    }
    if (outputShape.length != 2 ||
        outputShape[0] != 1 ||
        outputShape[1] != AppConfig.expectedOutputClasses) {
      throw StateError(
        'Expected model output shape '
        '[1, ${AppConfig.expectedOutputClasses}], found $outputShape.',
      );
    }
    if (metadata.modelMetadata['total_labels'] !=
        AppConfig.expectedOutputClasses) {
      throw StateError('Model metadata total_labels must be 76.');
    }
    if (metadata.modelMetadata['input_dtype'] != 'float32' ||
        metadata.modelMetadata['output_dtype'] != 'float32') {
      throw StateError('The deployed TFLite contract must use float32 I/O.');
    }
    _validatePreprocessing(metadata.preprocessingConfig);
  }

  void _validatePreprocessing(Map<String, Object?> config) {
    final sourceShape = _readIntList(config, 'source_sequence_shape');
    final featureOrder = _readObjectStringList(config, 'feature_order');
    final leftHandIndices = _readIntList(config, 'left_hand_indices');
    final rightHandIndices = _readIntList(config, 'right_hand_indices');
    if (!_sameOrder(sourceShape, const <int>[60, 126]) ||
        config['feature_width'] != AppConfig.expectedInputWidth ||
        !_sameOrder(featureOrder, const <String>[
          'mean',
          'std',
          'min',
          'max',
          'first_frame',
          'last_frame',
        ]) ||
        config['standard_deviation_ddof'] != 0 ||
        !_sameOrder(leftHandIndices, const <int>[0, 62]) ||
        !_sameOrder(rightHandIndices, const <int>[63, 125])) {
      throw StateError('Preprocessing metadata does not match Flutter.');
    }
  }

  List<int> _readIntList(Map<String, Object?> data, String key) {
    final values = data[key];
    if (values is! List) {
      throw StateError('$key is missing or is not a list.');
    }
    return values
        .map((value) => (value as num).toInt())
        .toList(growable: false);
  }

  List<String> _readObjectStringList(Map<String, Object?> data, String key) {
    final values = data[key];
    if (values is! List) {
      throw StateError('$key is missing or is not a list.');
    }
    return values.map((value) => value.toString()).toList(growable: false);
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

  List<String> _readStringList(Map<String, dynamic> data, String key) {
    final values = data[key];
    if (values is! List) {
      throw StateError('$key is missing or is not a list.');
    }
    return values.map((value) => value.toString()).toList(growable: false);
  }
}
