import 'dart:convert';

import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../config/banking_intent_scope.dart';
import '../models/manual_field_config.dart';
import '../models/query_configuration.dart';

class QueryConfigurationException implements Exception {
  const QueryConfigurationException(this.message);

  final String message;

  @override
  String toString() => 'Query configuration error: $message';
}

class QueryConfigurationService {
  QueryConfigurationService({AssetBundle? assetBundle})
    : _assetBundle = assetBundle ?? rootBundle;

  final AssetBundle _assetBundle;

  Future<QueryConfiguration> load() async {
    try {
      final raw = await _assetBundle.loadString(AppConfig.bankingQueriesAsset);
      final decoded = jsonDecode(raw);
      if (decoded is! Map<String, Object?>) {
        throw const FormatException(
          'The top-level JSON value must be an object.',
        );
      }
      final configuration = QueryConfiguration.fromJson(decoded);
      final result = QueryConfigurationValidator.validate(configuration);
      if (!result.isValid) {
        throw QueryConfigurationException(result.errors.join(' '));
      }
      return configuration;
    } on QueryConfigurationException {
      rethrow;
    } on Object catch (error) {
      throw QueryConfigurationException(error.toString());
    }
  }
}

class QueryConfigurationValidator {
  static QueryValidationResult validate(QueryConfiguration configuration) {
    final errors = <String>[];
    if (configuration.schemaVersion != 1) {
      errors.add('schema_version must be 1.');
    }
    if (configuration.domain != 'banking') {
      errors.add('domain must be banking.');
    }

    final intentIds = configuration.intents.map((intent) => intent.id).toList();
    final duplicateIntents = _duplicates(intentIds);
    if (duplicateIntents.isNotEmpty) {
      errors.add('Duplicate intent IDs: ${duplicateIntents.join(', ')}.');
    }

    final expected = BankingIntentScope.frozenIntents.toSet();
    final actual = intentIds.toSet();
    final missing = expected.difference(actual).toList()..sort();
    final extra = actual.difference(expected).toList()..sort();
    if (missing.isNotEmpty) {
      errors.add('Missing frozen intents: ${missing.join(', ')}.');
    }
    if (extra.isNotEmpty) {
      errors.add('Unexpected intents: ${extra.join(', ')}.');
    }
    if (intentIds.length == BankingIntentScope.frozenIntents.length &&
        !_sameOrder(intentIds, BankingIntentScope.frozenIntents)) {
      errors.add('Intent IDs must follow the frozen model output order.');
    }
    if (actual.any(BankingIntentScope.removedIntents.contains)) {
      errors.add('Removed banking intents are not allowed.');
    }
    if (actual.any((id) => RegExp(r'^[A-Z]$').hasMatch(id))) {
      errors.add('Alphabet labels are not allowed.');
    }
    if (actual.any((id) => RegExp(r'^[0-9]$').hasMatch(id))) {
      errors.add('Digit labels are not allowed.');
    }

    for (final intent in configuration.intents) {
      if (intent.displayName.trim().isEmpty) {
        errors.add('${intent.id}: display_name is required.');
      }
      if (intent.queries.length < 3 || intent.queries.length > 6) {
        errors.add('${intent.id}: query count must be between 3 and 6.');
      }

      final queryIds = intent.queries.map((query) => query.id).toList();
      final duplicateQueries = _duplicates(queryIds);
      if (duplicateQueries.isNotEmpty) {
        errors.add(
          '${intent.id}: duplicate query IDs: ${duplicateQueries.join(', ')}.',
        );
      }

      final fieldIds = intent.manualFields.map((field) => field.id).toList();
      final duplicateFields = _duplicates(fieldIds);
      if (duplicateFields.isNotEmpty) {
        errors.add(
          '${intent.id}: duplicate manual field IDs: ${duplicateFields.join(', ')}.',
        );
      }
      final knownFields = fieldIds.toSet();
      for (final query in intent.queries) {
        if (query.text.trim().isEmpty) {
          errors.add('${intent.id}/${query.id}: query text is required.');
        }
        final duplicateReferences = _duplicates(query.manualFieldIds);
        if (duplicateReferences.isNotEmpty) {
          errors.add(
            '${intent.id}/${query.id}: duplicate manual field references.',
          );
        }
        final unknownFields = query.manualFieldIds
            .where((fieldId) => !knownFields.contains(fieldId))
            .toList();
        if (unknownFields.isNotEmpty) {
          errors.add(
            '${intent.id}/${query.id}: unknown manual fields: '
            '${unknownFields.join(', ')}.',
          );
        }
      }
      for (final field in intent.manualFields) {
        if (field.maximumLength != null && field.maximumLength! <= 0) {
          errors.add(
            '${intent.id}/${field.id}: maximum_length must be positive.',
          );
        }
        if (field.type == ManualFieldType.select && field.options.isEmpty) {
          errors.add(
            '${intent.id}/${field.id}: select fields require options.',
          );
        }
        if (field.displayMasked && !field.sensitive) {
          errors.add(
            '${intent.id}/${field.id}: display_masked requires sensitive=true.',
          );
        }
      }
    }
    return QueryValidationResult(List<String>.unmodifiable(errors));
  }

  static Set<String> _duplicates(Iterable<String> values) {
    final seen = <String>{};
    return values.where((value) => !seen.add(value)).toSet();
  }

  static bool _sameOrder(List<String> left, List<String> right) {
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
}
