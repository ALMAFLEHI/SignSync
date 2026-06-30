import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/services.dart';

import '../config/app_config.dart';

class LabelMetadata {
  const LabelMetadata({
    required this.labels,
    required this.labelMapping,
    required this.allLabels,
    required this.normalModeLabels,
    required this.numberModeLabels,
    required this.modelMetadata,
  });

  final List<String> labels;
  final Map<String, int> labelMapping;
  final List<String> allLabels;
  final List<String> normalModeLabels;
  final List<String> numberModeLabels;
  final Map<String, Object?> modelMetadata;

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

      final metadata = LabelMetadata(
        labels: labels,
        labelMapping: labelMapping,
        allLabels: _readStringList(groups, 'all_labels'),
        normalModeLabels: _readStringList(groups, 'normal_mode'),
        numberModeLabels: _readStringList(groups, 'number_mode'),
        modelMetadata: modelMetadata,
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
      throw StateError('Expected 86 labels, found ${metadata.labels.length}.');
    }
    if (metadata.allLabels.length != AppConfig.expectedOutputClasses) {
      throw StateError(
        'Expected 86 all_labels entries, found ${metadata.allLabels.length}.',
      );
    }
    if (metadata.normalModeLabels.length !=
        AppConfig.expectedNormalModeLabels) {
      throw StateError(
        'Expected 76 normal mode labels, found ${metadata.normalModeLabels.length}.',
      );
    }
    if (metadata.numberModeLabels.length !=
        AppConfig.expectedNumberModeLabels) {
      throw StateError(
        'Expected 10 number mode labels, found ${metadata.numberModeLabels.length}.',
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
        'Expected model output shape [1, 86], found $outputShape.',
      );
    }
  }

  List<String> _readStringList(Map<String, dynamic> data, String key) {
    final values = data[key];
    if (values is! List) {
      throw StateError('$key is missing or is not a list.');
    }
    return values.map((value) => value.toString()).toList(growable: false);
  }
}
