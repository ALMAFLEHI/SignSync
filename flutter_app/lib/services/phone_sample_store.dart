import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';

class PhoneSampleStore {
  PhoneSampleStore({required this.directoryPath});

  static const String participantId = 'P02_PHONE';
  static const String source = 'phone_live_landmark';
  static const String device = 'Samsung Android phone';
  static const List<String> weakLabels = <String>[
    'transfer',
    'address_change',
    'document',
    'signature',
    'atm',
  ];
  static const int targetSamplesPerLabel = 20;

  final String directoryPath;

  Directory get directory => Directory(directoryPath);

  Future<Map<String, int>> countSamplesByLabel() async {
    await directory.create(recursive: true);
    final counts = {for (final label in weakLabels) label: 0};
    await for (final entity in directory.list()) {
      if (entity is! File || !entity.path.endsWith('.json')) {
        continue;
      }
      final fileName = entity.uri.pathSegments.last;
      for (final label in weakLabels) {
        if (fileName.startsWith('${participantId}_${label}_R')) {
          counts[label] = (counts[label] ?? 0) + 1;
        }
      }
    }
    return counts;
  }

  Future<PhoneSampleSaveResult> saveSample({
    required String label,
    required List<List<double>> frames,
  }) async {
    if (!weakLabels.contains(label)) {
      throw ArgumentError('Unsupported Sprint 2.16A weak label: $label');
    }
    _validateFrames(frames);
    await directory.create(recursive: true);

    final repetition = await _nextRepetition(label);
    final sampleId =
        '${participantId}_${label}_R${_formatRepetition(repetition)}';
    final file = File(
      '${directory.path}${Platform.pathSeparator}$sampleId.json',
    );
    if (await file.exists()) {
      throw StateError('Phone sample already exists: ${file.path}');
    }

    final payload = <String, Object?>{
      'sample_id': sampleId,
      'participant_id': participantId,
      'label': label,
      'repetition': repetition,
      'source': source,
      'device': device,
      'frames': frames,
      'frame_count': AppConfig.expectedFrameCount,
      'frame_width': AppConfig.expectedFrameWidth,
      'created_at': DateTime.now().toUtc().toIso8601String(),
      'notes':
          'Captured from live Android camera using MediaPipe HandLandmarker',
    };
    await file.writeAsString(
      const JsonEncoder.withIndent('  ').convert(payload),
      encoding: utf8,
    );

    return PhoneSampleSaveResult(
      sampleId: sampleId,
      label: label,
      repetition: repetition,
      path: file.path,
    );
  }

  Future<int> _nextRepetition(String label) async {
    var maxRepetition = 0;
    final pattern = RegExp(
      '^${RegExp.escape(participantId)}_${RegExp.escape(label)}_R(\\d+)\\.json\$',
    );
    await for (final entity in directory.list()) {
      if (entity is! File) {
        continue;
      }
      final match = pattern.firstMatch(entity.uri.pathSegments.last);
      if (match == null) {
        continue;
      }
      final repetition = int.tryParse(match.group(1) ?? '') ?? 0;
      if (repetition > maxRepetition) {
        maxRepetition = repetition;
      }
    }
    return maxRepetition + 1;
  }

  void _validateFrames(List<List<double>> frames) {
    if (frames.length != AppConfig.expectedFrameCount) {
      throw ArgumentError(
        'Expected ${AppConfig.expectedFrameCount} frames, found ${frames.length}.',
      );
    }
    for (var index = 0; index < frames.length; index += 1) {
      final frame = frames[index];
      if (frame.length != AppConfig.expectedFrameWidth) {
        throw ArgumentError(
          'Frame $index must contain ${AppConfig.expectedFrameWidth} values, found ${frame.length}.',
        );
      }
      if (frame.any((value) => !value.isFinite)) {
        throw ArgumentError('Frame $index contains NaN or infinite values.');
      }
    }
  }

  String _formatRepetition(int repetition) {
    return repetition.toString().padLeft(2, '0');
  }
}

class PhoneSampleSaveResult {
  const PhoneSampleSaveResult({
    required this.sampleId,
    required this.label,
    required this.repetition,
    required this.path,
  });

  final String sampleId;
  final String label;
  final int repetition;
  final String path;
}
