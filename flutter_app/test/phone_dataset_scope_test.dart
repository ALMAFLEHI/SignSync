import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/config/phone_dataset_scope.dart';
import 'package:flutter_app/services/phone_sample_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Sprint 2.16B scope reconstructs active V3 in exact order', () {
    PhoneDatasetScope.validate();
    final remaining = PhoneDatasetScope.sprint216BRemainingBankingIntents;
    final pilot = PhoneDatasetScope.sprint216APilotIntents;

    expect(remaining, hasLength(36));
    expect(remaining.toSet(), hasLength(36));
    expect(
      pilot,
      orderedEquals(<String>['transfer', 'document', 'signature', 'atm']),
    );
    expect(pilot.toSet().intersection(remaining.toSet()), isEmpty);
    expect(
      PhoneDatasetScope.activeBankingIntentsV3.where(
        (label) => !pilot.contains(label),
      ),
      orderedEquals(remaining),
    );
    expect(<String>{...pilot, ...remaining}, hasLength(40));
  });

  test('Sprint 2.16B scope excludes removed labels, alphabet, and digits', () {
    final remaining = PhoneDatasetScope.sprint216BRemainingBankingIntents;

    expect(
      remaining.toSet().intersection(
        PhoneDatasetScope.removedBankingIntents.toSet(),
      ),
      isEmpty,
    );
    expect(remaining, everyElement(isNot(matches(RegExp(r'^[A-Z]$')))));
    expect(remaining, everyElement(isNot(matches(RegExp(r'^[0-9]$')))));
  });

  test('Sprint 2.16B collection arithmetic and model contract are fixed', () {
    expect(PhoneDatasetScope.samplesPerLabel, 25);
    expect(PhoneDatasetScope.newSampleTarget, 900);
    expect(PhoneDatasetScope.finalBankingPhoneTarget, 1000);
    expect(PhoneSampleStore.sprint216BCollectionLabels, hasLength(36));
    expect(AppConfig.expectedInputWidth, 756);
    expect(AppConfig.expectedOutputClasses, 40);
  });
}
