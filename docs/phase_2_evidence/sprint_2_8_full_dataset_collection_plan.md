# Sprint 2.8 Full Dataset Collection Plan

## Sprint Goal
Prepare a controlled, manual collection workflow for the labels that were not included in the Sprint 2.3 trial dataset.

## Collection Scope
- Source vocabulary size: 56 labels.
- Trial labels already covered: 11.
- Remaining labels: 45.
- Repetitions per remaining label: 10.
- Expected new videos: 450.
- Participant: P02.
- Camera index: 1.
- Recording tool: `ml/src/collect_video.py`.

## Remaining Label Strategy
The 45 remaining labels are derived by subtracting the 11 existing trial labels from `ALL_LABELS` while preserving the original label order. This keeps the Sprint 2.8 scope separate from the recorded trial dataset.

## Recording Workflow
1. Run the syntax check.
2. Generate the 450 manual commands.
3. Run the interactive runner dry-run and review the command order.
4. When ready, run the interactive runner and confirm each recording manually.
5. Run the verification script after all recordings are complete.

## Recording Quality Rules
- Use a clean background.
- Use stable lighting.
- Keep hand(s) visible.
- Keep the gesture centered.
- Use the same camera angle and distance as much as possible.
- Prefer a consistent body position.
- For one-hand signs, use the same hand consistently.
- For two-hand signs, ensure both hands are clearly visible.
- Re-record a sample if it is blurry, cropped, hidden, or too fast.

## Later Expansion
A future extension can add repetitions 11-20 to reach 20 recordings per remaining label. That extension is not part of Sprint 2.8.

## Sprint Boundary
Sprint 2.8 prepares and validates the collection workflow only. It does not automatically record videos, modify the Sprint 2.5 dataset, retrain models, create TensorFlow Lite files, create Flutter integration, or start Sprint 2.9.

## Acceptance Criteria
- [x] Config for remaining labels exists.
- [x] Full command generator exists.
- [x] Interactive runner exists.
- [x] Verification script exists.
- [x] README exists.
- [x] Plan document exists.
- [x] Checklist exists.
- [x] PowerShell command file exists after command generation.
- [x] Markdown command file exists after command generation.
- [x] Syntax checks pass.
- [x] Dry-run works.
- [x] No recording is performed automatically.
- [x] No Sprint 2.9 work starts.
