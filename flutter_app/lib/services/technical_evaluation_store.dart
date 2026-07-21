import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:csv/csv.dart';
import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../models/technical_evaluation.dart';

abstract interface class TechnicalEvaluationPersistence {
  Future<Map<String, dynamic>?> loadProgress(String sessionId);

  Future<void> saveProgress(String sessionId, Map<String, dynamic> payload);

  Future<EvaluationExportResult> exportCompletedSession({
    required String sessionId,
    required List<EvaluationTrialResult> results,
    required List<EvaluationTechnicalEvent> technicalEvents,
    required Map<String, Object?> sessionMetadata,
  });

  Future<void> clearSession(String sessionId, {required bool confirmed});
}

class TechnicalEvaluationPlatformService {
  const TechnicalEvaluationPlatformService();

  static const MethodChannel _channel = MethodChannel(
    'signsync/live_landmarks',
  );

  Future<String> getEvaluationDirectory() async {
    if (!Platform.isAndroid) {
      throw UnsupportedError('Sprint 2.19 evaluation requires Android.');
    }
    final path = await _channel.invokeMethod<String>('getEvaluationDirectory');
    if (path == null || path.isEmpty) {
      throw StateError('Android evaluation directory was not returned.');
    }
    return path;
  }

  Future<EvaluationDeviceInfo> getDeviceInfo() async {
    if (!Platform.isAndroid) {
      throw UnsupportedError('Sprint 2.19 device metadata requires Android.');
    }
    final value = await _channel.invokeMapMethod<String, Object?>(
      'getEvaluationDeviceInfo',
    );
    if (value == null) {
      throw StateError('Android device metadata was not returned.');
    }
    return EvaluationDeviceInfo(
      deviceModel: value['device_model'].toString(),
      androidVersion: value['android_version'].toString(),
      androidApiLevel: (value['android_api_level'] as num).toInt(),
      packageId: value['app_package_id'].toString(),
      appVersion: value['app_version'].toString(),
      buildNumber: value['build_number'].toString(),
    );
  }
}

class FileTechnicalEvaluationPersistence
    implements TechnicalEvaluationPersistence {
  FileTechnicalEvaluationPersistence({required this.directoryPath});

  final String directoryPath;

  Directory get directory => Directory(directoryPath);

  static const List<String> trialColumns = <String>[
    'protocol_version',
    'session_id',
    'trial_number',
    'block_number',
    'condition',
    'intended_label',
    'intended_label_index',
    'predicted_label',
    'predicted_label_index',
    'confidence',
    'second_label',
    'second_confidence',
    'confidence_margin',
    'accepted',
    'rejected',
    'correct_top1',
    'correct_and_accepted',
    'incorrect_and_accepted',
    'correct_but_rejected',
    'capture_duration_ms',
    'average_capture_fps',
    'feature_computation_ms',
    'tflite_inference_ms',
    'prediction_processing_ms',
    'model_load_ms',
    'technical_status',
    'device_model',
    'android_version',
    'active_model_version',
    'active_model_sha256',
    'confidence_threshold',
    'timestamp',
    'notes',
  ];

  static const List<String> technicalEventColumns = <String>[
    'session_id',
    'event_number',
    'trial_number',
    'block_number',
    'condition',
    'intended_label',
    'event_type',
    'message',
    'timestamp',
  ];

  @override
  Future<Map<String, dynamic>?> loadProgress(String sessionId) async {
    final file = File(_progressPath(sessionId));
    if (!await file.exists()) {
      return null;
    }
    final value = jsonDecode(await file.readAsString(encoding: utf8));
    if (value is! Map<String, dynamic>) {
      throw const FormatException('Evaluation progress must be a JSON object.');
    }
    return value;
  }

  @override
  Future<void> saveProgress(
    String sessionId,
    Map<String, dynamic> payload,
  ) async {
    await directory.create(recursive: true);
    await _writeAtomic(
      File(_progressPath(sessionId)),
      '${const JsonEncoder.withIndent('  ').convert(payload)}\n',
    );
  }

  @override
  Future<EvaluationExportResult> exportCompletedSession({
    required String sessionId,
    required List<EvaluationTrialResult> results,
    required List<EvaluationTechnicalEvent> technicalEvents,
    required Map<String, Object?> sessionMetadata,
  }) async {
    if (results.length != AppConfig.evaluationTrialCount) {
      throw StateError('Only a complete 400-trial session may be exported.');
    }
    await directory.create(recursive: true);
    final safeSessionId = sanitizeSessionId(sessionId);
    final base = 'sprint_2_19_$safeSessionId';
    final trialCsv = File(
      '${directory.path}${Platform.pathSeparator}${base}_live_trials.csv',
    );
    final trialJson = File(
      '${directory.path}${Platform.pathSeparator}${base}_live_trials.json',
    );
    final eventsCsv = File(
      '${directory.path}${Platform.pathSeparator}${base}_technical_events.csv',
    );
    final metadataJson = File(
      '${directory.path}${Platform.pathSeparator}${base}_session_metadata.json',
    );
    final checksumFile = File(
      '${directory.path}${Platform.pathSeparator}${base}_SHA256SUMS.txt',
    );

    final trialMaps = results.map((result) => result.toJson()).toList();
    final eventMaps = technicalEvents.map((event) => event.toJson()).toList();
    await _writeAtomic(trialCsv, _toCsv(trialColumns, trialMaps));
    await _writeAtomic(
      trialJson,
      '${const JsonEncoder.withIndent('  ').convert(trialMaps)}\n',
    );
    await _writeAtomic(eventsCsv, _toCsv(technicalEventColumns, eventMaps));

    final exportHashes = <String, String>{
      trialCsv.uri.pathSegments.last: await _sha256File(trialCsv),
      trialJson.uri.pathSegments.last: await _sha256File(trialJson),
      eventsCsv.uri.pathSegments.last: await _sha256File(eventsCsv),
    };
    final completedMetadata = <String, Object?>{
      ...sessionMetadata,
      'actual_valid_trial_count': results.length,
      'technical_event_count': technicalEvents.length,
      'export_file_sha256': exportHashes,
    };
    await _writeAtomic(
      metadataJson,
      '${const JsonEncoder.withIndent('  ').convert(completedMetadata)}\n',
    );
    exportHashes[metadataJson.uri.pathSegments.last] = await _sha256File(
      metadataJson,
    );
    await _writeAtomic(
      checksumFile,
      '${exportHashes.entries.map((entry) => '${entry.value}  ${entry.key}').join('\n')}\n',
    );
    final files = <File>[
      trialCsv,
      trialJson,
      eventsCsv,
      metadataJson,
      checksumFile,
    ];
    return EvaluationExportResult(
      directoryPath: directory.path,
      files: files.map((file) => file.path).toList(growable: false),
      sha256ByFile: Map<String, String>.unmodifiable(exportHashes),
    );
  }

  @override
  Future<void> clearSession(String sessionId, {required bool confirmed}) async {
    if (!confirmed) {
      throw StateError('Explicit confirmation is required to clear a session.');
    }
    final safe = sanitizeSessionId(sessionId);
    if (!await directory.exists()) {
      return;
    }
    await for (final entity in directory.list(followLinks: false)) {
      if (entity is File && entity.uri.pathSegments.last.contains(safe)) {
        await entity.delete();
      }
    }
  }

  String _progressPath(String sessionId) {
    final safe = sanitizeSessionId(sessionId);
    return '${directory.path}${Platform.pathSeparator}sprint_2_19_${safe}_progress.json';
  }

  static String sanitizeSessionId(String value) {
    final sanitized = value.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
    if (sanitized.isEmpty || sanitized.length > 64) {
      throw ArgumentError('Session ID must contain 1-64 safe characters.');
    }
    return sanitized;
  }

  static String _toCsv(List<String> columns, List<Map<String, Object>> rows) {
    final table = <List<Object?>>[
      columns,
      ...rows.map(
        (row) => columns.map((column) => row[column]).toList(growable: false),
      ),
    ];
    return const ListToCsvConverter(
      eol: '\n',
      fieldDelimiter: ',',
      textDelimiter: '"',
    ).convert(table);
  }

  static Future<void> _writeAtomic(File target, String content) async {
    final temporary = File(
      '${target.path}.${DateTime.now().microsecondsSinceEpoch}.tmp',
    );
    await temporary.writeAsString(content, encoding: utf8, flush: true);
    try {
      await temporary.rename(target.path);
    } on FileSystemException {
      if (await target.exists()) {
        await target.delete();
      }
      await temporary.rename(target.path);
    }
  }

  static Future<String> _sha256File(File file) async {
    final digest = await sha256.bind(file.openRead()).first;
    return digest.toString().toUpperCase();
  }
}
