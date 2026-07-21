import 'package:flutter/foundation.dart';

import '../config/app_config.dart';
import '../models/live_prediction_session.dart';
import '../models/technical_evaluation.dart';
import '../services/technical_evaluation_store.dart';

enum EvaluationRecordOutcome { warmUpRecorded, formalResultRecorded }

class TechnicalEvaluationController extends ChangeNotifier {
  TechnicalEvaluationController({required List<EvaluationTrial> schedule})
    : _schedule = List<EvaluationTrial>.unmodifiable(schedule) {
    if (_schedule.length != AppConfig.evaluationTrialCount) {
      throw ArgumentError('The evaluation controller requires 400 trials.');
    }
  }

  final List<EvaluationTrial> _schedule;
  final List<EvaluationTrialResult> _results = <EvaluationTrialResult>[];
  final List<EvaluationTechnicalEvent> _technicalEvents =
      <EvaluationTechnicalEvent>[];

  TechnicalEvaluationPersistence? _persistence;
  EvaluationDeviceInfo? _device;
  String? _sessionId;
  DateTime? _startedAt;
  DateTime? _completedAt;
  int _currentTrialIndex = 0;
  int _warmUpsCompleted = 0;
  bool _paused = false;
  bool _awaitingAdvance = false;
  EvaluationExportResult? _lastExport;

  bool get hasSession => _sessionId != null;
  String? get sessionId => _sessionId;
  EvaluationDeviceInfo? get device => _device;
  int get warmUpsCompleted => _warmUpsCompleted;
  int get completedTrialCount => _results.length;
  int get technicalEventCount => _technicalEvents.length;
  bool get paused => _paused;
  bool get awaitingAdvance => _awaitingAdvance;
  bool get warmUpComplete =>
      _warmUpsCompleted >= AppConfig.evaluationWarmUpCount;
  bool get isComplete =>
      _results.length == AppConfig.evaluationTrialCount &&
      _currentTrialIndex == AppConfig.evaluationTrialCount &&
      !_awaitingAdvance;
  bool get captureLocked => _paused || _awaitingAdvance || isComplete;
  List<EvaluationTrialResult> get results =>
      List<EvaluationTrialResult>.unmodifiable(_results);
  List<EvaluationTechnicalEvent> get technicalEvents =>
      List<EvaluationTechnicalEvent>.unmodifiable(_technicalEvents);
  EvaluationTrialResult? get latestResult =>
      _results.isEmpty ? null : _results.last;
  EvaluationExportResult? get lastExport => _lastExport;

  EvaluationTrial? get currentTrial {
    if (!hasSession || _currentTrialIndex >= _schedule.length) {
      return null;
    }
    return _schedule[_currentTrialIndex];
  }

  Future<void> startOrResume({
    required String sessionId,
    required TechnicalEvaluationPersistence persistence,
    required EvaluationDeviceInfo device,
  }) async {
    if (hasSession) {
      throw StateError('An evaluation session is already active.');
    }
    final safeSessionId = FileTechnicalEvaluationPersistence.sanitizeSessionId(
      sessionId,
    );
    _persistence = persistence;
    final progress = await persistence.loadProgress(safeSessionId);
    if (progress == null) {
      _sessionId = safeSessionId;
      _device = device;
      _startedAt = DateTime.now().toUtc();
      await _persist();
    } else {
      _restore(progress, expectedSessionId: safeSessionId);
      if (_device?.packageId != AppConfig.androidPackageId) {
        throw StateError('Stored evaluation package ID is invalid.');
      }
    }
    notifyListeners();
  }

  Future<EvaluationRecordOutcome> recordLiveSession(
    LivePredictionSession liveSession,
  ) async {
    _requireActiveCaptureState();
    if (!warmUpComplete) {
      _warmUpsCompleted += 1;
      await _persist();
      notifyListeners();
      return EvaluationRecordOutcome.warmUpRecorded;
    }
    final trial = currentTrial;
    if (trial == null ||
        _results.any(
          (result) => result.trial.trialNumber == trial.trialNumber,
        )) {
      throw StateError('The scheduled trial has already been recorded.');
    }
    final result = EvaluationTrialResult.fromLiveSession(
      protocolVersion: AppConfig.evaluationProtocolVersion,
      sessionId: _sessionId!,
      trial: trial,
      liveSession: liveSession,
      device: _device!,
      activeModelVersion: AppConfig.modelVersion,
      activeModelSha256: AppConfig.activeDynamicModelSha256,
      confidenceThreshold: AppConfig.bankingIntentConfidenceThreshold,
    );
    _results.add(result);
    _awaitingAdvance = true;
    await _persist();
    notifyListeners();
    return EvaluationRecordOutcome.formalResultRecorded;
  }

  Future<void> confirmAndAdvance() async {
    if (!_awaitingAdvance || currentTrial == null) {
      throw StateError(
        'No immutable trial result is waiting for confirmation.',
      );
    }
    _awaitingAdvance = false;
    _currentTrialIndex += 1;
    if (_currentTrialIndex == AppConfig.evaluationTrialCount) {
      _completedAt = DateTime.now().toUtc();
    }
    await _persist();
    notifyListeners();
  }

  Future<void> pause() async {
    if (!hasSession || isComplete) {
      return;
    }
    _paused = true;
    await _persist();
    notifyListeners();
  }

  Future<void> resume() async {
    if (!hasSession || isComplete) {
      return;
    }
    _paused = false;
    final trial = currentTrial;
    _technicalEvents.add(
      EvaluationTechnicalEvent(
        sessionId: _sessionId!,
        eventNumber: _technicalEvents.length + 1,
        trialNumber: trial?.trialNumber ?? 0,
        blockNumber: trial?.blockNumber ?? 0,
        condition: trial?.condition ?? EvaluationCondition.standard,
        intendedLabel: trial?.intendedLabel ?? 'session_complete',
        eventType: 'evaluation_resumed',
        message: 'Evaluation resumed from locally persisted progress.',
        timestamp: DateTime.now().toUtc(),
      ),
    );
    await _persist();
    notifyListeners();
  }

  Future<void> recordTechnicalFailure({
    required String eventType,
    required String message,
  }) async {
    if (!hasSession) {
      return;
    }
    final trial = currentTrial;
    _technicalEvents.add(
      EvaluationTechnicalEvent(
        sessionId: _sessionId!,
        eventNumber: _technicalEvents.length + 1,
        trialNumber: warmUpComplete ? (trial?.trialNumber ?? 0) : 0,
        blockNumber: warmUpComplete ? (trial?.blockNumber ?? 0) : 0,
        condition: trial?.condition ?? EvaluationCondition.standard,
        intendedLabel: warmUpComplete
            ? (trial?.intendedLabel ?? 'session_complete')
            : 'excluded_warm_up',
        eventType: eventType,
        message: message,
        timestamp: DateTime.now().toUtc(),
      ),
    );
    await _persist();
    notifyListeners();
  }

  Future<EvaluationExportResult> exportCompletedSession() async {
    if (!isComplete || _completedAt == null) {
      throw StateError('Complete and confirm all 400 trials before export.');
    }
    final export = await _persistence!.exportCompletedSession(
      sessionId: _sessionId!,
      results: results,
      technicalEvents: technicalEvents,
      sessionMetadata: <String, Object?>{
        'protocol_version': AppConfig.evaluationProtocolVersion,
        'session_id': _sessionId,
        'trial_schedule_sha256': AppConfig.evaluationScheduleSha256,
        'model_version': AppConfig.modelVersion,
        'model_sha256': AppConfig.activeDynamicModelSha256,
        'label_file_sha256': AppConfig.activeLabelsSha256,
        'deployment_manifest_sha256': AppConfig.deploymentManifestSha256,
        'confidence_threshold': AppConfig.bankingIntentConfidenceThreshold,
        ..._device!.toJson(),
        'evaluation_started_at': _startedAt!.toIso8601String(),
        'evaluation_completed_at': _completedAt!.toIso8601String(),
        'expected_trial_count': AppConfig.evaluationTrialCount,
        'warm_up_trials_excluded': AppConfig.evaluationWarmUpCount,
      },
    );
    _lastExport = export;
    notifyListeners();
    return export;
  }

  Future<void> clearSession({required bool confirmed}) async {
    if (!hasSession) {
      return;
    }
    await _persistence!.clearSession(_sessionId!, confirmed: confirmed);
    _results.clear();
    _technicalEvents.clear();
    _persistence = null;
    _device = null;
    _sessionId = null;
    _startedAt = null;
    _completedAt = null;
    _currentTrialIndex = 0;
    _warmUpsCompleted = 0;
    _paused = false;
    _awaitingAdvance = false;
    _lastExport = null;
    notifyListeners();
  }

  void _requireActiveCaptureState() {
    if (!hasSession || _device == null || _persistence == null) {
      throw StateError('Start or resume an evaluation session first.');
    }
    if (_paused || _awaitingAdvance || isComplete) {
      throw StateError('The evaluation is paused or awaiting confirmation.');
    }
  }

  Future<void> _persist() async {
    await _persistence!.saveProgress(_sessionId!, <String, dynamic>{
      'protocol_version': AppConfig.evaluationProtocolVersion,
      'session_id': _sessionId,
      'trial_schedule_sha256': AppConfig.evaluationScheduleSha256,
      'active_model_version': AppConfig.modelVersion,
      'active_model_sha256': AppConfig.activeDynamicModelSha256,
      'confidence_threshold': AppConfig.bankingIntentConfidenceThreshold,
      'device': _device!.toJson(),
      'started_at': _startedAt!.toIso8601String(),
      'completed_at': _completedAt?.toIso8601String(),
      'current_trial_index': _currentTrialIndex,
      'warm_ups_completed': _warmUpsCompleted,
      'paused': _paused,
      'awaiting_advance': _awaitingAdvance,
      'results': _results.map((result) => result.toJson()).toList(),
      'technical_events': _technicalEvents
          .map((event) => event.toJson())
          .toList(),
    });
  }

  void _restore(
    Map<String, dynamic> progress, {
    required String expectedSessionId,
  }) {
    if (progress['protocol_version'] != AppConfig.evaluationProtocolVersion ||
        progress['session_id'] != expectedSessionId ||
        progress['trial_schedule_sha256'] !=
            AppConfig.evaluationScheduleSha256 ||
        progress['active_model_version'] != AppConfig.modelVersion ||
        progress['active_model_sha256'] != AppConfig.activeDynamicModelSha256 ||
        progress['confidence_threshold'] !=
            AppConfig.bankingIntentConfidenceThreshold) {
      throw StateError(
        'Stored evaluation progress fails frozen integrity checks.',
      );
    }
    _sessionId = expectedSessionId;
    _device = EvaluationDeviceInfo.fromJson(
      Map<String, dynamic>.from(progress['device'] as Map),
    );
    _startedAt = DateTime.parse(progress['started_at'] as String);
    _completedAt = progress['completed_at'] == null
        ? null
        : DateTime.parse(progress['completed_at'] as String);
    _currentTrialIndex = progress['current_trial_index'] as int;
    _warmUpsCompleted = progress['warm_ups_completed'] as int;
    _paused = progress['paused'] as bool;
    _awaitingAdvance = progress['awaiting_advance'] as bool;
    _results
      ..clear()
      ..addAll(
        (progress['results'] as List).map(
          (value) => EvaluationTrialResult.fromJson(
            Map<String, dynamic>.from(value as Map),
          ),
        ),
      );
    _technicalEvents
      ..clear()
      ..addAll(
        (progress['technical_events'] as List).map(
          (value) => EvaluationTechnicalEvent.fromJson(
            Map<String, dynamic>.from(value as Map),
          ),
        ),
      );
    if (_results.length != _currentTrialIndex + (_awaitingAdvance ? 1 : 0) ||
        _currentTrialIndex < 0 ||
        _currentTrialIndex > AppConfig.evaluationTrialCount ||
        _warmUpsCompleted < 0 ||
        _warmUpsCompleted > AppConfig.evaluationWarmUpCount) {
      throw StateError(
        'Stored evaluation progress is internally inconsistent.',
      );
    }
  }
}
