# SignSync Sprint 2.3 Trial Dataset Plan

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.3: Trial Dataset Collection

## Sprint Goal
Create a controlled trial dataset workflow before full dataset collection. The trial verifies that the recording process works correctly across alphabet, digit, and banking intent labels.

## Trial Labels
- A
- B
- C
- 0
- 1
- 2
- deposit
- withdraw
- balance
- help
- confirm

## Total Expected Videos
- Trial labels: 11
- Repetitions per label: 5
- Total expected videos: 55

## Recording Environment Rules
- Use a clean background.
- Use bright stable lighting.
- Keep the hand clearly visible.
- Keep the hand inside the frame.
- Keep distance around 0.8 to 1.2 meters from the camera.
- Avoid fast motion.
- Re-record samples if the hand is blurry, cut off, or hidden.

## Camera Index Note
Use camera index 1 for this laptop:

```powershell
--camera-index 1
```

## Participant ID Rule
Use `P02` as the default Sprint 2.3 trial participant ID to avoid mixing trial recordings with Sprint 2.2 tool-test recordings.

## Naming Format
Each video must follow this naming pattern:

```text
P02_[label]_RXX.mp4
```

Example:

```text
P02_deposit_R01.mp4
```

## Metadata Expectation
Each successful recording must append one row to `ml/metadata.csv` with:

- `sample_id`
- `participant_id`
- `label`
- `repetition`
- `video_path`
- empty `landmark_path`
- `status` set to `raw_recorded`
- notes containing Sprint 2.3 trial dataset information

## Quality Rules
- Check the hand is visible for the full gesture.
- Re-record if the hand leaves the frame.
- Re-record if lighting changes sharply.
- Re-record if the video is blurry or interrupted.
- Keep participant position consistent across recordings.

## Acceptance Criteria
- [ ] All 55 trial videos are recorded.
- [ ] All trial videos use participant ID `P02`.
- [ ] All trial videos are saved under the correct label folders.
- [ ] All metadata rows are appended correctly.
- [ ] No duplicate trial sample IDs exist in metadata.
- [ ] `check_trial_dataset.py` passes.
- [ ] Evidence screenshots are saved.
- [ ] No landmark extraction, model training, or Flutter integration is added in this sprint.
