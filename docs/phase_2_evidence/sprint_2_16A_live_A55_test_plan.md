# Sprint 2.16A Controlled Live Samsung Galaxy A55 Test Plan

## Status

Ready for manual execution. No live result is recorded yet.

## Purpose

Validate the reviewed Experiment B model in the real Android camera pipeline before Sprint 2.16A is closed. These are fresh live attempts and must not reuse saved phone collection samples.

## Deployed Contract

- Primary model: `flutter_app/assets/models/model_dynamic_range.tflite`
- Input: float32 `[1, 756]`
- Output: float32 `[1, 76]`
- Modes: Alphabet 26, Number 10, Banking Intent 40
- Banking confidence threshold: 0.70
- Minimum top-two gap: 0.15
- Stabilization: two agreeing predictions from three captures
- Ambiguous or low-confidence result: `Try Again`

## Test Set

| Group | Labels | Attempts Per Label | Total |
| --- | --- | ---: | ---: |
| Pilot banking intents | transfer, document, signature, atm | 10 | 40 |
| Alphabet control | A | 5 | 5 |
| Number control | 7 | 5 | 5 |
| Banking controls | deposit, payment, balance | 5 | 15 |
| Total | 9 labels | | 65 |

Each logged attempt is one completed stabilized decision. Let the app collect its normal three-capture window; do not disable stabilization.

## Procedure

1. Install the current Android debug build on the Samsung Galaxy A55.
2. Confirm the app reports the Experiment B dynamic-range model and opens the live camera.
3. Use Alphabet Mode for `A`, Number Mode for `7`, and Banking Intent Mode for every banking label.
4. Use fresh live signing attempts in normal demonstration lighting and framing.
5. Complete 10 attempts for each pilot label and 5 for each control label.
6. For every completed stabilized decision, record raw top one/top two labels and confidence, gap, final display, Try Again status, correctness, and relevant notes.
7. Restart the capture after each logged attempt. Do not import or replay stored landmark JSON files.
8. Record failures exactly as observed. Do not repeat an attempt merely to replace an incorrect result.

## Success Criteria

Pilot labels should achieve at least 8/10 correct per label. Repeated high-confidence wrong predictions are not acceptable. `Try Again` is acceptable for genuinely ambiguous captures. `transfer`, `signature`, and `atm` should retain the clear offline improvement. Test `document` carefully because one untouched phone test sample was confused with `card`.

Controls `A`, `7`, `deposit`, and `balance` should show no meaningful regression. Test `payment` carefully because its small offline control score declined to 50%. Any repeated control-label failure pattern blocks Sprint 2.16B until investigated.

## Decision Rule

Sprint 2.16B may begin only if the 65-attempt evidence demonstrates clear live improvement without serious control-label regression. Sprint 2.16A remains open until the completed CSV and live findings are reviewed.
