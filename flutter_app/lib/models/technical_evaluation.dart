import 'live_prediction_session.dart';

enum EvaluationCondition {
  standard('standard', 'Standard'),
  mildVariation('mild_variation', 'Mild variation');

  const EvaluationCondition(this.storageValue, this.displayName);

  final String storageValue;
  final String displayName;

  static EvaluationCondition fromStorage(String value) {
    return values.firstWhere(
      (condition) => condition.storageValue == value,
      orElse: () =>
          throw FormatException('Unsupported evaluation condition: $value'),
    );
  }
}

class EvaluationTrial {
  const EvaluationTrial({
    required this.trialNumber,
    required this.blockNumber,
    required this.condition,
    required this.intendedLabel,
    required this.intendedLabelIndex,
    required this.scheduledOrder,
    required this.randomSeed,
  });

  final int trialNumber;
  final int blockNumber;
  final EvaluationCondition condition;
  final String intendedLabel;
  final int intendedLabelIndex;
  final int scheduledOrder;
  final int randomSeed;

  Map<String, Object> toJson() => <String, Object>{
    'trial_number': trialNumber,
    'block_number': blockNumber,
    'condition': condition.storageValue,
    'intended_label': intendedLabel,
    'intended_label_index': intendedLabelIndex,
    'scheduled_order': scheduledOrder,
    'random_seed': randomSeed,
  };

  factory EvaluationTrial.fromJson(Map<String, dynamic> json) {
    return EvaluationTrial(
      trialNumber: json['trial_number'] as int,
      blockNumber: json['block_number'] as int,
      condition: EvaluationCondition.fromStorage(json['condition'] as String),
      intendedLabel: json['intended_label'] as String,
      intendedLabelIndex: json['intended_label_index'] as int,
      scheduledOrder: json['scheduled_order'] as int,
      randomSeed: json['random_seed'] as int,
    );
  }
}

class EvaluationDeviceInfo {
  const EvaluationDeviceInfo({
    required this.deviceModel,
    required this.androidVersion,
    required this.androidApiLevel,
    required this.packageId,
    required this.appVersion,
    required this.buildNumber,
  });

  final String deviceModel;
  final String androidVersion;
  final int androidApiLevel;
  final String packageId;
  final String appVersion;
  final String buildNumber;

  Map<String, Object> toJson() => <String, Object>{
    'device_model': deviceModel,
    'android_version': androidVersion,
    'android_api_level': androidApiLevel,
    'app_package_id': packageId,
    'app_version': appVersion,
    'build_number': buildNumber,
  };

  factory EvaluationDeviceInfo.fromJson(Map<String, dynamic> json) {
    return EvaluationDeviceInfo(
      deviceModel: json['device_model'] as String,
      androidVersion: json['android_version'] as String,
      androidApiLevel: json['android_api_level'] as int,
      packageId: json['app_package_id'] as String,
      appVersion: json['app_version'] as String,
      buildNumber: json['build_number'] as String,
    );
  }
}

class EvaluationTrialResult {
  const EvaluationTrialResult({
    required this.protocolVersion,
    required this.sessionId,
    required this.trial,
    required this.predictedLabel,
    required this.predictedLabelIndex,
    required this.confidence,
    required this.secondLabel,
    required this.secondConfidence,
    required this.confidenceMargin,
    required this.accepted,
    required this.correctTop1,
    required this.captureDurationMs,
    required this.averageCaptureFps,
    required this.featureComputationMs,
    required this.tfliteInferenceMs,
    required this.predictionProcessingMs,
    required this.modelLoadMs,
    required this.device,
    required this.activeModelVersion,
    required this.activeModelSha256,
    required this.confidenceThreshold,
    required this.timestamp,
    required this.notes,
  });

  final String protocolVersion;
  final String sessionId;
  final EvaluationTrial trial;
  final String predictedLabel;
  final int predictedLabelIndex;
  final double confidence;
  final String secondLabel;
  final double secondConfidence;
  final double confidenceMargin;
  final bool accepted;
  final bool correctTop1;
  final int captureDurationMs;
  final double averageCaptureFps;
  final double featureComputationMs;
  final double tfliteInferenceMs;
  final double predictionProcessingMs;
  final double modelLoadMs;
  final EvaluationDeviceInfo device;
  final String activeModelVersion;
  final String activeModelSha256;
  final double confidenceThreshold;
  final DateTime timestamp;
  final String notes;

  bool get rejected => !accepted;
  bool get correctAndAccepted => correctTop1 && accepted;
  bool get incorrectAndAccepted => !correctTop1 && accepted;
  bool get correctButRejected => correctTop1 && !accepted;

  factory EvaluationTrialResult.fromLiveSession({
    required String protocolVersion,
    required String sessionId,
    required EvaluationTrial trial,
    required LivePredictionSession liveSession,
    required EvaluationDeviceInfo device,
    required String activeModelVersion,
    required String activeModelSha256,
    required double confidenceThreshold,
    DateTime? timestamp,
  }) {
    final prediction = liveSession.prediction;
    if (prediction.rawTopPredictions.length < 2) {
      throw StateError('Evaluation requires top-1 and top-2 predictions.');
    }
    final top1 = prediction.rawTopPredictions[0];
    final top2 = prediction.rawTopPredictions[1];
    return EvaluationTrialResult(
      protocolVersion: protocolVersion,
      sessionId: sessionId,
      trial: trial,
      predictedLabel: top1.label,
      predictedLabelIndex: top1.index,
      confidence: top1.probability,
      secondLabel: top2.label,
      secondConfidence: top2.probability,
      confidenceMargin: top1.probability - top2.probability,
      accepted: prediction.decision.accepted,
      correctTop1: top1.label == trial.intendedLabel,
      captureDurationMs: liveSession.captureMetrics.captureDurationMs,
      averageCaptureFps: liveSession.captureMetrics.averageFps,
      featureComputationMs: liveSession.featureComputationPreciseMs,
      tfliteInferenceMs: liveSession.inferencePreciseMs,
      predictionProcessingMs: liveSession.predictionProcessingPreciseMs,
      modelLoadMs: liveSession.modelLoadMs,
      device: device,
      activeModelVersion: activeModelVersion,
      activeModelSha256: activeModelSha256,
      confidenceThreshold: confidenceThreshold,
      timestamp: timestamp ?? DateTime.now().toUtc(),
      notes: '',
    );
  }

  Map<String, Object> toJson() => <String, Object>{
    'protocol_version': protocolVersion,
    'session_id': sessionId,
    ...trial.toJson(),
    'predicted_label': predictedLabel,
    'predicted_label_index': predictedLabelIndex,
    'confidence': confidence,
    'second_label': secondLabel,
    'second_confidence': secondConfidence,
    'confidence_margin': confidenceMargin,
    'accepted': accepted,
    'rejected': rejected,
    'correct_top1': correctTop1,
    'correct_and_accepted': correctAndAccepted,
    'incorrect_and_accepted': incorrectAndAccepted,
    'correct_but_rejected': correctButRejected,
    'capture_duration_ms': captureDurationMs,
    'average_capture_fps': averageCaptureFps,
    'feature_computation_ms': featureComputationMs,
    'tflite_inference_ms': tfliteInferenceMs,
    'prediction_processing_ms': predictionProcessingMs,
    'model_load_ms': modelLoadMs,
    'technical_status': 'valid_inference',
    'device_model': device.deviceModel,
    'android_version': device.androidVersion,
    'android_api_level': device.androidApiLevel,
    'app_package_id': device.packageId,
    'app_version': device.appVersion,
    'build_number': device.buildNumber,
    'active_model_version': activeModelVersion,
    'active_model_sha256': activeModelSha256,
    'confidence_threshold': confidenceThreshold,
    'timestamp': timestamp.toIso8601String(),
    'notes': notes,
  };

  factory EvaluationTrialResult.fromJson(Map<String, dynamic> json) {
    return EvaluationTrialResult(
      protocolVersion: json['protocol_version'] as String,
      sessionId: json['session_id'] as String,
      trial: EvaluationTrial.fromJson(json),
      predictedLabel: json['predicted_label'] as String,
      predictedLabelIndex: json['predicted_label_index'] as int,
      confidence: (json['confidence'] as num).toDouble(),
      secondLabel: json['second_label'] as String,
      secondConfidence: (json['second_confidence'] as num).toDouble(),
      confidenceMargin: (json['confidence_margin'] as num).toDouble(),
      accepted: json['accepted'] as bool,
      correctTop1: json['correct_top1'] as bool,
      captureDurationMs: json['capture_duration_ms'] as int,
      averageCaptureFps: (json['average_capture_fps'] as num).toDouble(),
      featureComputationMs: (json['feature_computation_ms'] as num).toDouble(),
      tfliteInferenceMs: (json['tflite_inference_ms'] as num).toDouble(),
      predictionProcessingMs: (json['prediction_processing_ms'] as num)
          .toDouble(),
      modelLoadMs: (json['model_load_ms'] as num).toDouble(),
      device: EvaluationDeviceInfo(
        deviceModel: json['device_model'] as String,
        androidVersion: json['android_version'] as String,
        androidApiLevel: (json['android_api_level'] as int?) ?? 0,
        packageId: (json['app_package_id'] as String?) ?? '',
        appVersion: (json['app_version'] as String?) ?? '',
        buildNumber: (json['build_number'] as String?) ?? '',
      ),
      activeModelVersion: json['active_model_version'] as String,
      activeModelSha256: json['active_model_sha256'] as String,
      confidenceThreshold: (json['confidence_threshold'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
      notes: (json['notes'] as String?) ?? '',
    );
  }
}

class EvaluationTechnicalEvent {
  const EvaluationTechnicalEvent({
    required this.sessionId,
    required this.eventNumber,
    required this.trialNumber,
    required this.blockNumber,
    required this.condition,
    required this.intendedLabel,
    required this.eventType,
    required this.message,
    required this.timestamp,
  });

  final String sessionId;
  final int eventNumber;
  final int trialNumber;
  final int blockNumber;
  final EvaluationCondition condition;
  final String intendedLabel;
  final String eventType;
  final String message;
  final DateTime timestamp;

  Map<String, Object> toJson() => <String, Object>{
    'session_id': sessionId,
    'event_number': eventNumber,
    'trial_number': trialNumber,
    'block_number': blockNumber,
    'condition': condition.storageValue,
    'intended_label': intendedLabel,
    'event_type': eventType,
    'message': message,
    'timestamp': timestamp.toIso8601String(),
  };

  factory EvaluationTechnicalEvent.fromJson(Map<String, dynamic> json) {
    return EvaluationTechnicalEvent(
      sessionId: json['session_id'] as String,
      eventNumber: json['event_number'] as int,
      trialNumber: json['trial_number'] as int,
      blockNumber: json['block_number'] as int,
      condition: EvaluationCondition.fromStorage(json['condition'] as String),
      intendedLabel: json['intended_label'] as String,
      eventType: json['event_type'] as String,
      message: json['message'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}

class EvaluationExportResult {
  const EvaluationExportResult({
    required this.directoryPath,
    required this.files,
    required this.sha256ByFile,
  });

  final String directoryPath;
  final List<String> files;
  final Map<String, String> sha256ByFile;
}
