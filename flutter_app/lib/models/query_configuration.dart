import 'manual_field_config.dart';

class BankingQueryOption {
  const BankingQueryOption({
    required this.id,
    required this.text,
    required this.manualFieldIds,
  });

  final String id;
  final String text;
  final List<String> manualFieldIds;

  factory BankingQueryOption.fromJson(Map<String, Object?> json) {
    return BankingQueryOption(
      id: _requiredString(json, 'id'),
      text: _requiredString(json, 'text'),
      manualFieldIds: _requiredStringList(json, 'manual_field_ids'),
    );
  }
}

class BankingIntentConfig {
  const BankingIntentConfig({
    required this.id,
    required this.displayName,
    required this.description,
    required this.queries,
    required this.manualFields,
  });

  final String id;
  final String displayName;
  final String description;
  final List<BankingQueryOption> queries;
  final List<ManualFieldConfig> manualFields;

  factory BankingIntentConfig.fromJson(Map<String, Object?> json) {
    return BankingIntentConfig(
      id: _requiredString(json, 'id'),
      displayName: _requiredString(json, 'display_name'),
      description: _requiredString(json, 'description'),
      queries: _objectList(
        json,
        'queries',
      ).map(BankingQueryOption.fromJson).toList(growable: false),
      manualFields: _objectList(
        json,
        'manual_fields',
      ).map(ManualFieldConfig.fromJson).toList(growable: false),
    );
  }
}

class QueryConfiguration {
  const QueryConfiguration({
    required this.schemaVersion,
    required this.domain,
    required this.intents,
  });

  final int schemaVersion;
  final String domain;
  final List<BankingIntentConfig> intents;

  factory QueryConfiguration.fromJson(Map<String, Object?> json) {
    final schemaVersion = json['schema_version'];
    if (schemaVersion is! int) {
      throw const FormatException('schema_version must be an integer.');
    }
    return QueryConfiguration(
      schemaVersion: schemaVersion,
      domain: _requiredString(json, 'domain'),
      intents: _objectList(
        json,
        'intents',
      ).map(BankingIntentConfig.fromJson).toList(growable: false),
    );
  }
}

class QueryValidationResult {
  const QueryValidationResult(this.errors);

  final List<String> errors;

  bool get isValid => errors.isEmpty;
}

String _requiredString(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is! String || value.trim().isEmpty) {
    throw FormatException('$key must be a non-empty string.');
  }
  return value.trim();
}

List<String> _requiredStringList(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is! List<Object?>) {
    throw FormatException('$key must be a list.');
  }
  return List<String>.unmodifiable(
    value.map((item) {
      if (item is! String || item.trim().isEmpty) {
        throw FormatException('$key must contain non-empty strings.');
      }
      return item.trim();
    }),
  );
}

List<Map<String, Object?>> _objectList(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is! List<Object?>) {
    throw FormatException('$key must be a list.');
  }
  return value
      .map((item) {
        if (item is! Map<Object?, Object?>) {
          throw FormatException('$key must contain objects.');
        }
        return item.map((itemKey, itemValue) {
          if (itemKey is! String) {
            throw FormatException('$key object keys must be strings.');
          }
          return MapEntry(itemKey, itemValue);
        });
      })
      .toList(growable: false);
}
