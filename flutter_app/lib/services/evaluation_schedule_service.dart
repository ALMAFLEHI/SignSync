import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:csv/csv.dart';
import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../config/banking_intent_scope.dart';
import '../models/technical_evaluation.dart';

class EvaluationScheduleService {
  const EvaluationScheduleService();

  Future<List<EvaluationTrial>> loadFrozenSchedule() async {
    final raw = await rootBundle.loadString(AppConfig.evaluationScheduleAsset);
    final digest = sha256.convert(utf8.encode(raw)).toString().toUpperCase();
    if (digest != AppConfig.evaluationScheduleSha256) {
      throw StateError('Sprint 2.19 schedule hash verification failed.');
    }
    final table = const CsvToListConverter(eol: '\n').convert(raw);
    if (table.isEmpty) {
      throw const FormatException('Evaluation schedule is empty.');
    }
    final headers = table.first.map((value) => value.toString()).toList();
    final rows = table
        .skip(1)
        .map((values) {
          final row = <String, Object?>{
            for (var index = 0; index < headers.length; index += 1)
              headers[index]: values[index],
          };
          return EvaluationTrial(
            trialNumber: (row['trial_number'] as num).toInt(),
            blockNumber: (row['block_number'] as num).toInt(),
            condition: EvaluationCondition.fromStorage(
              row['condition'].toString(),
            ),
            intendedLabel: row['intended_label'].toString(),
            intendedLabelIndex: (row['intended_label_index'] as num).toInt(),
            scheduledOrder: (row['scheduled_order'] as num).toInt(),
            randomSeed: (row['random_seed'] as num).toInt(),
          );
        })
        .toList(growable: false);
    validate(rows);
    return rows;
  }

  List<EvaluationTrial> generate() {
    final generator = _XorShift32(AppConfig.evaluationRandomSeed);
    final labels = BankingIntentScope.frozenIntents;
    final labelToIndex = <String, int>{
      for (final entry in labels.indexed) entry.$2: entry.$1,
    };
    final rows = <EvaluationTrial>[];
    var trialNumber = 1;
    for (var block = 1; block <= 10; block += 1) {
      final randomized = List<String>.of(labels);
      for (var index = randomized.length - 1; index > 0; index -= 1) {
        final swapIndex = generator.nextUint32() % (index + 1);
        final value = randomized[index];
        randomized[index] = randomized[swapIndex];
        randomized[swapIndex] = value;
      }
      final condition = block <= 5
          ? EvaluationCondition.standard
          : EvaluationCondition.mildVariation;
      for (var order = 1; order <= randomized.length; order += 1) {
        final label = randomized[order - 1];
        rows.add(
          EvaluationTrial(
            trialNumber: trialNumber,
            blockNumber: block,
            condition: condition,
            intendedLabel: label,
            intendedLabelIndex: labelToIndex[label]!,
            scheduledOrder: order,
            randomSeed: AppConfig.evaluationRandomSeed,
          ),
        );
        trialNumber += 1;
      }
    }
    validate(rows);
    return List<EvaluationTrial>.unmodifiable(rows);
  }

  void validate(List<EvaluationTrial> schedule) {
    if (schedule.length != AppConfig.evaluationTrialCount) {
      throw StateError('Evaluation schedule must contain exactly 400 trials.');
    }
    final trialNumbers = schedule.map((trial) => trial.trialNumber).toSet();
    if (trialNumbers.length != schedule.length ||
        !trialNumbers.contains(1) ||
        !trialNumbers.contains(400)) {
      throw StateError('Evaluation trial numbers are missing or duplicated.');
    }
    for (var block = 1; block <= 10; block += 1) {
      final blockRows = schedule
          .where((trial) => trial.blockNumber == block)
          .toList(growable: false);
      if (blockRows.length != 40 ||
          blockRows.map((trial) => trial.intendedLabel).toSet().length != 40 ||
          !blockRows.every(
            (trial) =>
                trial.condition ==
                (block <= 5
                    ? EvaluationCondition.standard
                    : EvaluationCondition.mildVariation),
          )) {
        throw StateError('Evaluation block $block is not balanced.');
      }
    }
    for (final label in BankingIntentScope.frozenIntents) {
      final labelRows = schedule
          .where((trial) => trial.intendedLabel == label)
          .toList(growable: false);
      if (labelRows.length != 10 ||
          labelRows
                  .where(
                    (trial) => trial.condition == EvaluationCondition.standard,
                  )
                  .length !=
              5 ||
          labelRows
                  .where(
                    (trial) =>
                        trial.condition == EvaluationCondition.mildVariation,
                  )
                  .length !=
              5) {
        throw StateError('Evaluation label $label is not balanced.');
      }
    }
    if (!schedule.every(
      (trial) =>
          trial.randomSeed == AppConfig.evaluationRandomSeed &&
          BankingIntentScope.frozenIntents[trial.intendedLabelIndex] ==
              trial.intendedLabel,
    )) {
      throw StateError('Evaluation seed or frozen label order changed.');
    }
  }
}

class _XorShift32 {
  _XorShift32(int seed) : _state = seed;

  int _state;

  int nextUint32() {
    var value = _state;
    value ^= (value << 13) & 0xFFFFFFFF;
    value ^= value >>> 17;
    value ^= (value << 5) & 0xFFFFFFFF;
    _state = value & 0xFFFFFFFF;
    return _state;
  }
}
