import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_app/models/technical_evaluation.dart';
import 'package:flutter_app/services/evaluation_schedule_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('frozen schedule has deterministic balanced 400-trial design', () async {
    const service = EvaluationScheduleService();
    final loaded = await service.loadFrozenSchedule();
    final generated = service.generate();

    expect(loaded, hasLength(400));
    expect(
      jsonEncode(loaded.map((trial) => trial.toJson()).toList()),
      jsonEncode(generated.map((trial) => trial.toJson()).toList()),
    );
    expect(
      loaded.map((trial) => trial.blockNumber).toSet(),
      orderedEquals(<int>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    );

    for (var block = 1; block <= 10; block += 1) {
      final rows = loaded.where((trial) => trial.blockNumber == block).toList();
      expect(rows, hasLength(40));
      expect(
        rows.map((trial) => trial.intendedLabel).toSet(),
        equals(BankingIntentScope.frozenIntents.toSet()),
      );
      expect(
        rows.every(
          (trial) =>
              trial.condition ==
              (block <= 5
                  ? EvaluationCondition.standard
                  : EvaluationCondition.mildVariation),
        ),
        isTrue,
      );
    }
    for (final label in BankingIntentScope.frozenIntents) {
      final rows = loaded.where((trial) => trial.intendedLabel == label);
      expect(rows, hasLength(10));
      expect(
        rows.where((trial) => trial.condition == EvaluationCondition.standard),
        hasLength(5),
      );
      expect(
        rows.where(
          (trial) => trial.condition == EvaluationCondition.mildVariation,
        ),
        hasLength(5),
      );
    }
  });

  test('schedule bytes retain the frozen SHA-256', () {
    final bytes = File(AppConfig.evaluationScheduleAsset).readAsBytesSync();
    final digest = sha256.convert(bytes).toString().toUpperCase();
    expect(digest, AppConfig.evaluationScheduleSha256);
    expect(utf8.decode(bytes), contains('random_seed'));
    expect(AppConfig.evaluationRandomSeed, 21919);
  });
}
