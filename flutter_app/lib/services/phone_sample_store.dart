import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../config/phone_dataset_scope.dart';

class PhoneSampleStore {
  PhoneSampleStore({
    required this.directoryPath,
    this.collectionLabels = PhoneDatasetScope.sprint216BRemainingBankingIntents,
    this.protectedLabels = PhoneDatasetScope.sprint216APilotIntents,
    this.targetSamplesPerLabel = PhoneDatasetScope.samplesPerLabel,
  }) {
    PhoneDatasetScope.validate();
    if (collectionLabels.any(protectedLabels.contains)) {
      throw ArgumentError('Collection and protected labels cannot overlap.');
    }
  }

  static const String participantId = PhoneDatasetScope.participantId;
  static const String source = 'phone_live_landmark';
  static const String device = 'Samsung Android phone';

  // Historical public name retained for completed Sprint 2.16A code/tests.
  static const List<String> weakLabels =
      PhoneDatasetScope.sprint216APilotIntents;
  static const List<String> sprint216APilotLabels =
      PhoneDatasetScope.sprint216APilotIntents;
  static const List<String> sprint216BCollectionLabels =
      PhoneDatasetScope.sprint216BRemainingBankingIntents;
  static const int sprint216ATargetSamplesPerLabel = 25;
  static const int sprint216BTargetSamplesPerLabel =
      PhoneDatasetScope.samplesPerLabel;

  final String directoryPath;
  final List<String> collectionLabels;
  final List<String> protectedLabels;
  final int targetSamplesPerLabel;

  Directory get directory => Directory(directoryPath);

  Future<Map<String, int>> countSamplesByLabel() async {
    return (await scanProgress()).counts;
  }

  Future<PhoneSampleProgress> scanProgress() async {
    await directory.create(recursive: true);
    final repetitions = <String, Set<int>>{
      for (final label in collectionLabels) label: <int>{},
    };
    final invalidFiles = <String>[];
    final seenSampleIds = <String>{};

    await for (final entity in directory.list(followLinks: false)) {
      if (entity is! File || !entity.path.toLowerCase().endsWith('.json')) {
        continue;
      }
      final fileName = entity.uri.pathSegments.last;
      if (!_belongsToCollectionScope(fileName)) {
        continue;
      }
      try {
        final sample = await _readValidSample(entity);
        if (!seenSampleIds.add(sample.sampleId)) {
          throw const FormatException('duplicate sample_id');
        }
        final labelRepetitions = repetitions[sample.label]!;
        if (!labelRepetitions.add(sample.repetition)) {
          throw const FormatException('duplicate label/repetition');
        }
      } on Object catch (error) {
        invalidFiles.add('$fileName: $error');
      }
    }

    return PhoneSampleProgress(
      repetitions: {
        for (final entry in repetitions.entries)
          entry.key: Set<int>.unmodifiable(entry.value),
      },
      invalidFiles: List<String>.unmodifiable(invalidFiles),
      targetSamplesPerLabel: targetSamplesPerLabel,
    );
  }

  Future<int> nextMissingRepetition(String label) async {
    _validateCollectionLabel(label);
    final progress = await scanProgress();
    final repetitions = progress.repetitions[label] ?? const <int>{};
    for (
      var repetition = 1;
      repetition <= targetSamplesPerLabel;
      repetition += 1
    ) {
      if (!repetitions.contains(repetition)) {
        return repetition;
      }
    }
    throw StateError('$label already has R01-R25. Capture is blocked.');
  }

  Future<PhoneSampleSaveResult> saveSample({
    required String label,
    required List<List<double>> frames,
  }) async {
    _validateCollectionLabel(label);
    _validateFrames(frames);
    await directory.create(recursive: true);

    final repetition = await nextMissingRepetition(label);
    final sampleId =
        '${participantId}_${label}_R${formatRepetition(repetition)}';
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
      'sprint_id': PhoneDatasetScope.sprintId,
      'frames': frames,
      'frame_count': AppConfig.expectedFrameCount,
      'frame_width': AppConfig.expectedFrameWidth,
      'frame_dimension': AppConfig.expectedFrameWidth,
      'created_at': DateTime.now().toUtc().toIso8601String(),
      'notes':
          'Captured from live Android camera using MediaPipe HandLandmarker',
    };
    final temporaryFile = File(
      '${file.path}.${DateTime.now().microsecondsSinceEpoch}.tmp',
    );
    var createdByThisCall = false;
    try {
      await temporaryFile.writeAsString(
        const JsonEncoder.withIndent('  ').convert(payload),
        encoding: utf8,
        flush: true,
      );
      if (await file.exists()) {
        throw StateError('Phone sample appeared before save: ${file.path}');
      }
      await temporaryFile.rename(file.path);
      createdByThisCall = true;
      final saved = await _readValidSample(file);
      return PhoneSampleSaveResult(
        sampleId: saved.sampleId,
        label: saved.label,
        repetition: saved.repetition,
        path: file.path,
      );
    } on Object {
      if (await temporaryFile.exists()) {
        await temporaryFile.delete();
      }
      if (createdByThisCall && await file.exists()) {
        await file.delete();
      }
      rethrow;
    }
  }

  Future<PhoneSampleDeleteCandidate?> lastSavedSampleForLabel(
    String label,
  ) async {
    _validateCollectionLabel(label);
    if (!await directory.exists()) {
      return null;
    }
    final candidates = <PhoneSampleDeleteCandidate>[];
    await for (final entity in directory.list(followLinks: false)) {
      if (entity is! File || !entity.path.toLowerCase().endsWith('.json')) {
        continue;
      }
      try {
        final sample = await _readValidSample(entity);
        if (sample.label != label) {
          continue;
        }
        final stat = await entity.stat();
        candidates.add(
          PhoneSampleDeleteCandidate(
            sampleId: sample.sampleId,
            label: sample.label,
            repetition: sample.repetition,
            path: entity.path,
            modifiedAt: stat.modified,
          ),
        );
      } on Object {
        continue;
      }
    }
    if (candidates.isEmpty) {
      return null;
    }
    candidates.sort(
      (left, right) => right.modifiedAt.compareTo(left.modifiedAt),
    );
    return candidates.first;
  }

  Future<PhoneSampleDeleteCandidate> deleteLastSavedSample({
    required String label,
    required String expectedSampleId,
  }) async {
    _validateCollectionLabel(label);
    if (protectedLabels.contains(label)) {
      throw StateError('Sprint 2.16A pilot samples are protected.');
    }
    final candidate = await lastSavedSampleForLabel(label);
    if (candidate == null) {
      throw StateError('No valid saved sample exists for $label.');
    }
    if (candidate.sampleId != expectedSampleId) {
      throw StateError(
        'The most recent sample changed. Refresh before deleting.',
      );
    }
    final file = File(candidate.path);
    if (!await file.exists()) {
      throw StateError('Sample no longer exists: ${candidate.path}');
    }
    await file.delete();
    return candidate;
  }

  bool _belongsToCollectionScope(String fileName) {
    return collectionLabels.any(
      (label) => fileName.startsWith('${participantId}_${label}_R'),
    );
  }

  Future<_StoredPhoneSample> _readValidSample(File file) async {
    final payload = jsonDecode(await file.readAsString(encoding: utf8));
    if (payload is! Map<String, dynamic>) {
      throw const FormatException('JSON root must be an object');
    }
    final sampleId = payload['sample_id'];
    final participant = payload['participant_id'];
    final label = payload['label'];
    final repetition = payload['repetition'];
    final sampleSource = payload['source'];
    final sampleDevice = payload['device'];
    final frameCount = payload['frame_count'];
    final frameWidth = payload['frame_width'];
    final framesValue = payload['frames'];
    if (sampleId is! String ||
        participant != participantId ||
        label is! String ||
        !collectionLabels.contains(label) ||
        repetition is! int ||
        repetition < 1 ||
        repetition > targetSamplesPerLabel ||
        sampleSource != source ||
        sampleDevice is! String ||
        sampleDevice.isEmpty ||
        frameCount != AppConfig.expectedFrameCount ||
        frameWidth != AppConfig.expectedFrameWidth ||
        framesValue is! List<dynamic>) {
      throw const FormatException('sample metadata contract is invalid');
    }
    final expectedSampleId =
        '${participantId}_${label}_R${formatRepetition(repetition)}';
    if (sampleId != expectedSampleId ||
        file.uri.pathSegments.last != '$expectedSampleId.json') {
      throw const FormatException('sample ID or filename is invalid');
    }
    final frames = framesValue
        .map(
          (frame) => (frame as List<dynamic>)
              .map((value) => (value as num).toDouble())
              .toList(growable: false),
        )
        .toList(growable: false);
    _validateFrames(frames);
    return _StoredPhoneSample(
      sampleId: sampleId,
      label: label,
      repetition: repetition,
    );
  }

  void _validateCollectionLabel(String label) {
    if (protectedLabels.contains(label)) {
      throw ArgumentError('Sprint 2.16A pilot label is protected: $label');
    }
    if (!collectionLabels.contains(label)) {
      throw ArgumentError('Unsupported Sprint 2.16B label: $label');
    }
  }

  static void validateFrames(List<List<double>> frames) {
    _validateFrames(frames);
  }

  static void _validateFrames(List<List<double>> frames) {
    if (frames.length != AppConfig.expectedFrameCount) {
      throw ArgumentError(
        'Expected ${AppConfig.expectedFrameCount} frames, found ${frames.length}.',
      );
    }
    for (var index = 0; index < frames.length; index += 1) {
      final frame = frames[index];
      if (frame.length != AppConfig.expectedFrameWidth) {
        throw ArgumentError(
          'Frame $index must contain ${AppConfig.expectedFrameWidth} values, '
          'found ${frame.length}.',
        );
      }
      if (frame.any((value) => !value.isFinite)) {
        throw ArgumentError('Frame $index contains NaN or infinite values.');
      }
      if (frame.every((value) => value == 0.0)) {
        throw ArgumentError('Frame $index contains no detected hand.');
      }
    }
  }

  static String formatRepetition(int repetition) {
    return repetition.toString().padLeft(2, '0');
  }
}

class PhoneSampleProgress {
  const PhoneSampleProgress({
    required this.repetitions,
    required this.invalidFiles,
    required this.targetSamplesPerLabel,
  });

  final Map<String, Set<int>> repetitions;
  final List<String> invalidFiles;
  final int targetSamplesPerLabel;

  Map<String, int> get counts => {
    for (final entry in repetitions.entries) entry.key: entry.value.length,
  };

  int get totalValidSamples =>
      repetitions.values.fold(0, (total, values) => total + values.length);

  int get completedLabels => repetitions.values
      .where((values) => values.length == targetSamplesPerLabel)
      .length;

  bool isComplete(String label) =>
      (repetitions[label]?.length ?? 0) >= targetSamplesPerLabel;
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

class PhoneSampleDeleteCandidate extends PhoneSampleSaveResult {
  const PhoneSampleDeleteCandidate({
    required super.sampleId,
    required super.label,
    required super.repetition,
    required super.path,
    required this.modifiedAt,
  });

  final DateTime modifiedAt;
}

class _StoredPhoneSample {
  const _StoredPhoneSample({
    required this.sampleId,
    required this.label,
    required this.repetition,
  });

  final String sampleId;
  final String label;
  final int repetition;
}
