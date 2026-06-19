# Sprint 2.7 Full Dataset Recording Plan

## Coverage Summary
- Total scoped labels: 56
- Already recorded trial labels: 11
- Remaining labels: 45
- Already recorded: A, B, C, 0, 1, 2, deposit, withdraw, balance, help, confirm
- Remaining: D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, 3, 4, 5, 6, 7, 8, 9, transfer, account, card, pin, password, identity_verification, cash, receipt, fee, loan, savings, open_account, close_account, fraud, block_card

## Recommended Recording Stages
### Stage 1: Complete the First Full-Label Dataset
- Record all 45 remaining labels for participant P02.
- Record 5 repetitions per label first (225 new recordings).
- Use camera index 1.
- This completes one full-label dataset version with 56 labels.

### Stage 2: Increase Repetitions
- Add more repetitions when time allows.
- Recommended target: 10 to 20 repetitions per label.

### Stage 3: Add Participants
- Add more participants when possible.
- More participants improve generalization and enable cross-participant testing.

## Recording Quality Rules
- Use the same camera index 1.
- Keep the hand visible.
- Keep stable lighting.
- Keep a plain background.
- Keep the same distance from the camera.
- For static signs, hold the gesture clearly.
- For movement signs, perform the movement once clearly and hold the final position.
- Re-record if the hand is cut off or landmark detection will likely fail.

## Checks After Recording
- Confirm metadata rows are created correctly.
- Confirm every new video is clean and has no preview overlay.
- Extract and verify two-hand landmarks.
- Rebuild and verify the training dataset only after the recordings are complete.
- Keep raw videos and generated dataset files out of Git.

## Output Files
- Remaining labels CSV: docs/phase_2_evidence/sprint_2_7_remaining_labels.csv
- Recording plan CSV: docs/phase_2_evidence/sprint_2_7_full_dataset_recording_plan.csv
