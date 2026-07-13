# Sprint 2.16A Phone Collection Guide

## Labels and Target

Use `Phone Dataset Collection` on the Samsung Android phone and record only:

- `transfer`
- `document`
- `signature`
- `atm`

Record at least 20 samples per label. Thirty per label is optional. The minimum pilot total is 80.

## Capture Workflow

1. Select one active weak label.
2. Start the camera and perform the sign.
3. Tap `Capture & Save Sample`.
4. Wait for 60 frames and the saved JSON confirmation.
5. Repeat until the counter reaches at least 20.

Sample IDs use `P02_PHONE_<label>_Rxx`, such as `P02_PHONE_transfer_R01`. Every sample has participant `P02_PHONE`, source `phone_live_landmark`, 60 frames, and 126 finite values per frame. The collection page does not offer removed labels.

## Pull and Validate

```powershell
adb pull /storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples "D:\SWE  MOODLE\Year 3 Semester 2\FYP Part 2\SignSync\ml\data_phone\landmark_samples"
python ml/src/check_phone_landmark_samples.py
python ml/src/import_phone_landmark_samples.py
python ml/src/prepare_phone_augmented_dataset.py --participant P02_PHONE
python ml/src/check_phone_augmented_dataset.py
```

Only landmark JSON is saved. No raw video is stored or sent to a server.
