import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/banking_intent_scope.dart';
import 'package:flutter_app/controllers/technical_evaluation_controller.dart';
import 'package:flutter_app/models/live_prediction_session.dart';
import 'package:flutter_app/models/prediction_result.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/models/technical_evaluation.dart';
import 'package:flutter_app/services/evaluation_schedule_service.dart';
import 'package:flutter_app/services/technical_evaluation_store.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/final_technical_evaluation_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final schedule = const EvaluationScheduleService().generate();

  test(
    'warm-ups are excluded and immutable first results are retained',
    () async {
      final persistence = _MemoryPersistence();
      final controller = TechnicalEvaluationController(schedule: schedule);
      await controller.startOrResume(
        sessionId: 'a55_test',
        persistence: persistence,
        device: _device,
      );

      for (var index = 0; index < 5; index += 1) {
        final outcome = await controller.recordLiveSession(
          _session(label: 'deposit', confidence: 0.99),
        );
        expect(outcome, EvaluationRecordOutcome.warmUpRecorded);
      }
      expect(controller.warmUpComplete, isTrue);
      expect(controller.completedTrialCount, 0);
      expect(controller.currentTrial!.trialNumber, 1);

      await controller.recordTechnicalFailure(
        eventType: 'no_hands_detected',
        message: 'No hands detected before inference.',
      );
      expect(controller.technicalEventCount, 1);
      expect(controller.completedTrialCount, 0);

      final intended = controller.currentTrial!.intendedLabel;
      final wrong = intended == 'deposit' ? 'withdraw' : 'deposit';
      final outcome = await controller.recordLiveSession(
        _session(label: wrong, confidence: 0.79),
      );
      expect(outcome, EvaluationRecordOutcome.formalResultRecorded);
      expect(controller.completedTrialCount, 1);
      expect(controller.latestResult!.predictedLabel, wrong);
      expect(controller.latestResult!.accepted, isFalse);
      expect(controller.latestResult!.correctTop1, isFalse);
      expect(controller.awaitingAdvance, isTrue);
      await expectLater(
        controller.recordLiveSession(
          _session(label: intended, confidence: 0.99),
        ),
        throwsStateError,
      );
    },
  );

  test(
    'pause and resume restore progress without overwriting trials',
    () async {
      final persistence = _MemoryPersistence();
      final first = TechnicalEvaluationController(schedule: schedule);
      await first.startOrResume(
        sessionId: 'resume_test',
        persistence: persistence,
        device: _device,
      );
      for (var index = 0; index < 5; index += 1) {
        await first.recordLiveSession(
          _session(label: 'deposit', confidence: 0.99),
        );
      }
      await first.recordLiveSession(
        _session(label: first.currentTrial!.intendedLabel, confidence: 0.91),
      );
      await first.confirmAndAdvance();
      await first.pause();

      final resumed = TechnicalEvaluationController(schedule: schedule);
      await resumed.startOrResume(
        sessionId: 'resume_test',
        persistence: persistence,
        device: _device,
      );
      expect(resumed.paused, isTrue);
      expect(resumed.completedTrialCount, 1);
      expect(resumed.currentTrial!.trialNumber, 2);
      await resumed.resume();
      expect(resumed.paused, isFalse);
    },
  );

  testWidgets('progress header displays the scheduled condition and label', (
    tester,
  ) async {
    final controller = TechnicalEvaluationController(schedule: schedule);
    final persistence = _MemoryPersistence();
    await controller.startOrResume(
      sessionId: 'display_test',
      persistence: persistence,
      device: _device,
    );
    for (var index = 0; index < 5; index += 1) {
      await controller.recordLiveSession(
        _session(label: 'deposit', confidence: 0.99),
      );
    }
    final trial = controller.currentTrial!;
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: Scaffold(
          body: EvaluationProgressHeader(
            controller: controller,
            trial: trial,
            latest: null,
            status: 'Protocol ready.',
            error: null,
          ),
        ),
      ),
    );
    expect(
      find.text('${trial.condition.displayName}: ${trial.intendedLabel}'),
      findsOneWidget,
    );
    expect(find.text('Trial 1 / 400 - Block 1'), findsOneWidget);
  });

  test(
    'export schema is metadata-only and clearing needs confirmation',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'signsync_eval_test_',
      );
      addTearDown(() => directory.delete(recursive: true));
      final persistence = FileTechnicalEvaluationPersistence(
        directoryPath: directory.path,
      );
      final results = <EvaluationTrialResult>[
        for (final trial in schedule)
          EvaluationTrialResult.fromLiveSession(
            protocolVersion: AppConfig.evaluationProtocolVersion,
            sessionId: 'export_test',
            trial: trial,
            liveSession: _session(label: trial.intendedLabel, confidence: 0.95),
            device: _device,
            activeModelVersion: AppConfig.modelVersion,
            activeModelSha256: AppConfig.activeDynamicModelSha256,
            confidenceThreshold: AppConfig.bankingIntentConfidenceThreshold,
          ),
      ];
      final export = await persistence.exportCompletedSession(
        sessionId: 'export_test',
        results: results,
        technicalEvents: const <EvaluationTechnicalEvent>[],
        sessionMetadata: const <String, Object?>{},
      );
      final csvPath = export.files.firstWhere(
        (path) => path.endsWith('_live_trials.csv'),
      );
      final header = File(csvPath).readAsLinesSync().first.split(',');
      expect(
        header,
        orderedEquals(FileTechnicalEvaluationPersistence.trialColumns),
      );
      final normalized = header.join(' ').toLowerCase();
      for (final forbidden in <String>[
        'image_path',
        'video_path',
        'raw_frame',
        'landmarks',
        'feature_vector',
        'customer_name',
        'account_number_value',
      ]) {
        expect(normalized, isNot(contains(forbidden)));
      }
      expect(File(csvPath).readAsLinesSync(), hasLength(401));
      await expectLater(
        persistence.clearSession('export_test', confirmed: false),
        throwsStateError,
      );
      expect(File(csvPath).existsSync(), isTrue);
      await persistence.clearSession('export_test', confirmed: true);
      expect(File(csvPath).existsSync(), isFalse);
    },
  );
}

const _device = EvaluationDeviceInfo(
  deviceModel: 'SM-A556E',
  androidVersion: '16',
  androidApiLevel: 36,
  packageId: AppConfig.androidPackageId,
  appVersion: '1.0.0',
  buildNumber: '1',
);

LivePredictionSession _session({
  required String label,
  required double confidence,
}) {
  final index = BankingIntentScope.frozenIntents.indexOf(label);
  final secondLabel = label == 'deposit' ? 'withdraw' : 'deposit';
  final secondIndex = BankingIntentScope.frozenIntents.indexOf(secondLabel);
  final accepted = confidence >= AppConfig.bankingIntentConfidenceThreshold;
  final top1 = TopPrediction(
    label: label,
    probability: confidence,
    index: index,
  );
  final top2 = TopPrediction(
    label: secondLabel,
    probability: 1.0 - confidence,
    index: secondIndex,
  );
  return LivePredictionSession(
    prediction: PredictionResult(
      predictedLabel: accepted ? label : 'Try Again',
      confidence: confidence,
      decision: PredictionDecision(
        accepted: accepted,
        displayLabel: accepted ? label : 'Try Again',
        confidenceThreshold: AppConfig.bankingIntentConfidenceThreshold,
        minimumTop2Gap: AppConfig.minimumTop2Gap,
        top2Gap: confidence - (1.0 - confidence),
        reason: accepted ? null : 'below_threshold',
        secondPrediction: top2,
      ),
      topPredictions: <TopPrediction>[top1, top2],
      rawTopPredictions: <TopPrediction>[top1, top2],
      rawOutputLength: 40,
      selectedMode: SignMode.bankingIntent,
      modelAsset: AppConfig.dynamicRangeModelAsset,
    ),
    featureLength: 756,
    captureMetrics: const LiveCaptureMetrics(
      validFrameCount: 60,
      frameDimension: 126,
      captureDurationMs: 2000,
      averageFps: 30.0,
    ),
    featureComputationMs: 2,
    inferenceMs: 2,
    endToEndMs: 4,
    featureComputationPreciseMs: 1.5,
    inferencePreciseMs: 1.8,
    predictionProcessingPreciseMs: 3.7,
    modelLoadMs: 14.0,
  );
}

class _MemoryPersistence implements TechnicalEvaluationPersistence {
  Map<String, dynamic>? progress;

  @override
  Future<void> clearSession(String sessionId, {required bool confirmed}) async {
    if (!confirmed) {
      throw StateError('Confirmation required.');
    }
    progress = null;
  }

  @override
  Future<EvaluationExportResult> exportCompletedSession({
    required String sessionId,
    required List<EvaluationTrialResult> results,
    required List<EvaluationTechnicalEvent> technicalEvents,
    required Map<String, Object?> sessionMetadata,
  }) async {
    return const EvaluationExportResult(
      directoryPath: 'memory',
      files: <String>[],
      sha256ByFile: <String, String>{},
    );
  }

  @override
  Future<Map<String, dynamic>?> loadProgress(String sessionId) async {
    if (progress == null) {
      return null;
    }
    return jsonDecode(jsonEncode(progress)) as Map<String, dynamic>;
  }

  @override
  Future<void> saveProgress(
    String sessionId,
    Map<String, dynamic> payload,
  ) async {
    progress = jsonDecode(jsonEncode(payload)) as Map<String, dynamic>;
  }
}
