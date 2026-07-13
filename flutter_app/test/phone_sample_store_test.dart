import 'dart:convert';
import 'dart:io';

import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/phone_dataset_scope.dart';
import 'package:flutter_app/services/phone_sample_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late Directory temporaryDirectory;
  late PhoneSampleStore store;

  setUp(() async {
    temporaryDirectory = await Directory.systemTemp.createTemp(
      'signsync_2_16B_store_test_',
    );
    store = PhoneSampleStore(directoryPath: temporaryDirectory.path);
  });

  tearDown(() async {
    if (await temporaryDirectory.exists()) {
      await temporaryDirectory.delete(recursive: true);
    }
  });

  test(
    'uses the first missing repetition and preserves existing files',
    () async {
      await _writeSample(temporaryDirectory, 'deposit', 1);
      await _writeSample(temporaryDirectory, 'deposit', 2);
      final r04 = await _writeSample(temporaryDirectory, 'deposit', 4);
      final r04Before = await r04.readAsString();

      expect(await store.nextMissingRepetition('deposit'), 3);
      final saved = await store.saveSample(
        label: 'deposit',
        frames: _validFrames(),
      );

      expect(saved.sampleId, 'P02_PHONE_deposit_R03');
      expect(saved.repetition, 3);
      expect(await r04.readAsString(), r04Before);
      expect(
        await File(
          '${temporaryDirectory.path}/P02_PHONE_deposit_R03.json',
        ).exists(),
        isTrue,
      );
    },
  );

  test(
    'restores counters from valid files and ignores malformed files',
    () async {
      await _writeSample(temporaryDirectory, 'withdraw', 1);
      await _writeSample(temporaryDirectory, 'withdraw', 2);
      await File(
        '${temporaryDirectory.path}/P02_PHONE_withdraw_R03.json',
      ).writeAsString('{broken json');

      final firstProgress = await store.scanProgress();
      final restartedStore = PhoneSampleStore(
        directoryPath: temporaryDirectory.path,
      );
      final restartedProgress = await restartedStore.scanProgress();

      expect(firstProgress.counts['withdraw'], 2);
      expect(firstProgress.invalidFiles, hasLength(1));
      expect(restartedProgress.counts['withdraw'], 2);
      expect(restartedProgress.invalidFiles, hasLength(1));
    },
  );

  test('blocks capture after all R01-R25 files exist', () async {
    for (var repetition = 1; repetition <= 25; repetition += 1) {
      await _writeSample(temporaryDirectory, 'balance', repetition);
    }

    final progress = await store.scanProgress();

    expect(progress.isComplete('balance'), isTrue);
    expect(() => store.nextMissingRepetition('balance'), throwsStateError);
    expect(
      () => store.saveSample(label: 'balance', frames: _validFrames()),
      throwsStateError,
    );
  });

  test(
    'failed save does not increment progress or leave a temp file',
    () async {
      final invalidFrames = List<List<double>>.generate(
        AppConfig.expectedFrameCount,
        (_) => List<double>.filled(AppConfig.expectedFrameWidth, 0),
      );

      expect(
        () => store.saveSample(label: 'account', frames: invalidFrames),
        throwsArgumentError,
      );
      final progress = await store.scanProgress();
      final files = await temporaryDirectory.list().toList();

      expect(progress.counts['account'], 0);
      expect(files, isEmpty);
    },
  );

  test(
    'deletes only the confirmed last sample for the selected label',
    () async {
      await _writeSample(temporaryDirectory, 'card', 1);
      final second = await _writeSample(temporaryDirectory, 'card', 2);
      await _writePilotSample(temporaryDirectory, 'transfer', 25);
      await second.setLastModified(
        DateTime.now().add(const Duration(seconds: 2)),
      );
      final candidate = await store.lastSavedSampleForLabel('card');

      expect(candidate?.sampleId, 'P02_PHONE_card_R02');
      final deleted = await store.deleteLastSavedSample(
        label: 'card',
        expectedSampleId: candidate!.sampleId,
      );

      expect(deleted.sampleId, 'P02_PHONE_card_R02');
      expect(
        await File(
          '${temporaryDirectory.path}/P02_PHONE_card_R01.json',
        ).exists(),
        isTrue,
      );
      expect(
        await File(
          '${temporaryDirectory.path}/P02_PHONE_card_R02.json',
        ).exists(),
        isFalse,
      );
      expect(
        () => store.deleteLastSavedSample(
          label: 'transfer',
          expectedSampleId: 'P02_PHONE_transfer_R25',
        ),
        throwsArgumentError,
      );
      expect(
        await File(
          '${temporaryDirectory.path}/P02_PHONE_transfer_R25.json',
        ).exists(),
        isTrue,
      );
    },
  );
}

List<List<double>> _validFrames() {
  return List<List<double>>.generate(
    AppConfig.expectedFrameCount,
    (frameIndex) => List<double>.generate(
      AppConfig.expectedFrameWidth,
      (valueIndex) => valueIndex < 63 ? 0 : 0.1 + frameIndex / 1000,
    ),
  );
}

Future<File> _writeSample(Directory directory, String label, int repetition) {
  return _writePayload(
    directory: directory,
    label: label,
    repetition: repetition,
    sprintId: PhoneDatasetScope.sprintId,
  );
}

Future<File> _writePilotSample(
  Directory directory,
  String label,
  int repetition,
) {
  return _writePayload(
    directory: directory,
    label: label,
    repetition: repetition,
    sprintId: '2.16A',
  );
}

Future<File> _writePayload({
  required Directory directory,
  required String label,
  required int repetition,
  required String sprintId,
}) async {
  final sampleId =
      '${PhoneSampleStore.participantId}_${label}_R${PhoneSampleStore.formatRepetition(repetition)}';
  final file = File('${directory.path}/$sampleId.json');
  await file.writeAsString(
    jsonEncode(<String, Object?>{
      'sample_id': sampleId,
      'participant_id': PhoneSampleStore.participantId,
      'label': label,
      'repetition': repetition,
      'source': PhoneSampleStore.source,
      'device': PhoneSampleStore.device,
      'sprint_id': sprintId,
      'frame_count': AppConfig.expectedFrameCount,
      'frame_width': AppConfig.expectedFrameWidth,
      'frames': _validFrames(),
    }),
  );
  return file;
}
