# Sprint 2.16A Checklist

## Setup Completed

- [x] Kept old laptop-camera dataset unchanged.
- [x] Preserved 86-label model output contract.
- [x] Kept Alphabet Mode, Number Mode, and Banking Intent Mode.
- [x] Added confidence threshold logic.
- [x] Added top-2 gap check.
- [x] Added Try Again output for risky predictions.
- [x] Added 3-capture majority-vote stabilization.
- [x] Preserved raw and filtered top predictions for debugging.
- [x] Added Phone Dataset Collection page.
- [x] Added local phone landmark JSON save workflow.
- [x] Added Python phone sample validation script.
- [x] Added Python phone sample import script.
- [x] Added Python phone-augmented dataset preparation/check scripts.
- [x] Added collection guide and pending evidence reports.

## Pending Phone Data

- [ ] Record 20 phone samples for `transfer`.
- [ ] Record 20 phone samples for `address_change`.
- [ ] Record 20 phone samples for `document`.
- [ ] Record 20 phone samples for `signature`.
- [ ] Record 20 phone samples for `atm`.
- [ ] Pull samples from phone to `ml/data_phone/landmark_samples/`.
- [ ] Validate phone samples.
- [ ] Create mixed laptop + phone dataset.
- [ ] Retrain model.
- [ ] Export updated TFLite model.
- [ ] Update Flutter model assets.
- [ ] Retest weak labels on phone.

## Scope Guard

- [x] No fake phone samples created.
- [x] No raw videos saved.
- [x] No cloud/server processing added.
- [x] No Sprint 2.16B started.
- [x] No Sprint 2.17 started.
- [x] No 100% accuracy claim.
