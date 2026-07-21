import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_app/models/query_configuration.dart';
import 'package:flutter_app/services/query_configuration_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late QueryConfiguration configuration;

  setUpAll(() async {
    configuration = await QueryConfigurationService().load();
  });

  test('loads the valid local configuration for exactly 40 frozen intents', () {
    expect(configuration.schemaVersion, 1);
    expect(configuration.domain, 'banking');
    expect(configuration.intents, hasLength(40));
    expect(
      configuration.intents.map((intent) => intent.id).toList(),
      BankingIntentScope.frozenIntents,
    );
    expect(QueryConfigurationValidator.validate(configuration).isValid, isTrue);
  });

  test('contains no extra, alphabet, digit, or removed intent labels', () {
    final ids = configuration.intents.map((intent) => intent.id).toSet();
    expect(ids, BankingIntentScope.frozenIntents.toSet());
    expect(ids.any((id) => RegExp(r'^[A-Z]$').hasMatch(id)), isFalse);
    expect(ids.any((id) => RegExp(r'^[0-9]$').hasMatch(id)), isFalse);
    expect(ids.any(BankingIntentScope.removedIntents.contains), isFalse);
  });

  test('every intent has four distinct non-empty query options', () {
    for (final intent in configuration.intents) {
      expect(intent.queries, hasLength(4), reason: intent.id);
      expect(
        intent.queries.map((query) => query.id).toSet(),
        hasLength(intent.queries.length),
        reason: intent.id,
      );
      expect(
        intent.queries.every((query) => query.text.trim().isNotEmpty),
        isTrue,
        reason: intent.id,
      );
    }
  });

  test('manual fields are unique and every query reference resolves', () {
    for (final intent in configuration.intents) {
      final fieldIds = intent.manualFields.map((field) => field.id).toList();
      expect(fieldIds.toSet(), hasLength(fieldIds.length), reason: intent.id);
      for (final query in intent.queries) {
        expect(
          query.manualFieldIds.every(fieldIds.contains),
          isTrue,
          reason: '${intent.id}/${query.id}',
        );
      }
    }
  });

  test('unsupported manual field types fail strict parsing', () async {
    final decoded =
        jsonDecode(await rootBundle.loadString(AppConfig.bankingQueriesAsset))
            as Map<String, dynamic>;
    final intents = decoded['intents'] as List<dynamic>;
    final firstIntent = intents.first as Map<String, dynamic>;
    final fields = firstIntent['manual_fields'] as List<dynamic>;
    (fields.first as Map<String, dynamic>)['type'] = 'email';

    expect(
      () => QueryConfiguration.fromJson(decoded.cast<String, Object?>()),
      throwsFormatException,
    );
  });

  test(
    'duplicate intents and unknown manual field references are rejected',
    () async {
      final decoded =
          jsonDecode(await rootBundle.loadString(AppConfig.bankingQueriesAsset))
              as Map<String, dynamic>;
      final intents = decoded['intents'] as List<dynamic>;
      (intents[1] as Map<String, dynamic>)['id'] =
          (intents[0] as Map<String, dynamic>)['id'];
      final firstQueries =
          (intents[0] as Map<String, dynamic>)['queries'] as List<dynamic>;
      (firstQueries[0] as Map<String, dynamic>)['manual_field_ids'] = [
        'missing_field',
      ];

      final invalid = QueryConfiguration.fromJson(
        decoded.cast<String, Object?>(),
      );
      final result = QueryConfigurationValidator.validate(invalid);
      expect(result.isValid, isFalse);
      expect(result.errors.join(' '), contains('Duplicate intent IDs'));
      expect(result.errors.join(' '), contains('unknown manual fields'));
    },
  );

  test('no network, database, or cloud dependency was introduced', () {
    final pubspec = File('pubspec.yaml').readAsStringSync().toLowerCase();
    for (final forbidden in [
      'firebase_',
      'cloud_firestore',
      'sqflite',
      'sqlite',
      'mysql',
      'postgres',
      'package:http',
      'dio:',
    ]) {
      expect(pubspec, isNot(contains(forbidden)), reason: forbidden);
    }
  });
}
