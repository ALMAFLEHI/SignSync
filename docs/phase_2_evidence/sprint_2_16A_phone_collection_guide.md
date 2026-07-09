# Sprint 2.16A Phone Collection Guide

## Flutter App Workflow

1. Open the SignSync Flutter app on the Samsung Android phone.
2. Open `Phone Dataset Collection`.
3. Select one weak label:
   - `transfer`
   - `address_change`
   - `document`
   - `signature`
   - `atm`
4. Tap `Start Camera`.
5. Perform the selected sign.
6. Tap `Capture & Save Sample`.
7. Wait until the 60-frame buffer completes and the JSON file is saved.
8. Repeat until each weak label has at least 20 samples.

## Saved JSON Contract

Each file is saved as:

```json
{
  "sample_id": "P02_PHONE_transfer_R01",
  "participant_id": "P02_PHONE",
  "label": "transfer",
  "repetition": 1,
  "source": "phone_live_landmark",
  "device": "Samsung Android phone",
  "frames": [[126 values], "... 60 rows total ..."],
  "frame_count": 60,
  "frame_width": 126,
  "created_at": "...",
  "notes": "Captured from live Android camera using MediaPipe HandLandmarker"
}
```

## Android Save Path

The app saves samples under the Android app-specific external files directory:

```text
/storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples/
```

The exact path is displayed inside the collection page after the storage folder is prepared.

## Pull Samples To PC

Use ADB after recording:

```powershell
adb pull /storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples "D:\SWE  MOODLE\Year 3 Semester 2\FYP Part 2\SignSync\ml\data_phone\landmark_samples"
```

Then run:

```powershell
python ml/src/check_phone_landmark_samples.py
python ml/src/import_phone_landmark_samples.py
python ml/src/prepare_phone_augmented_dataset.py --participant P02_PHONE
python ml/src/check_phone_augmented_dataset.py
```

## Privacy Note

Only landmark JSON files are saved. No raw video is saved, uploaded, or sent to a server.
