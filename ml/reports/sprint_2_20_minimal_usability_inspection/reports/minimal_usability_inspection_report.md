# Sprint 2.20 Minimal Usability Inspection

## Status: COMPLETE WITH FORMATIVE LIMITATIONS

## Objective

Inspect whether the final guided banking workflow is understandable, consistent, readable, navigable, privacy-aware, recoverable, and free from major usability blockers. Recognition accuracy was not evaluated.

## Method and Evaluator

- External participants were unavailable.
- Evaluator count: **1**.
- Evaluator role: **developer/researcher**.
- Method: structured cognitive walkthrough, heuristic inspection, accessibility/privacy inspection, and automated Flutter workflow validation.
- Purpose: formative defect detection; results are not generalizable.
- No participant study was performed and no usability ratings, questionnaires, timings, comments, consent records, or SUS data were fabricated.

> This sprint used a formative researcher-led usability inspection and automated workflow validation. No external participants were available. The findings identify interface strengths and potential improvements but cannot replace future evaluation with Deaf and hard-of-hearing users, banking staff, and independent participants.

## Four Scenarios

- Scenario 1 - Account problem: **PASS**
- Scenario 2 - Transfer request: **PASS**
- Scenario 3 - Document request without populated manual details: **PARTIAL**
- Scenario 4 - Cancel and recovery: **PASS**

The document scenario safely omits empty optional details in review and banker view, but its protected query mapping references an optional `document_type` field. It therefore visits the optional-details page instead of directly bypassing it. This is a non-blocking severity-2 finding.

## Inspection Results

- Cognitive walkthrough: 64 PASS observations across 8 workflow steps.
- Heuristics: 10 PASS, 2 PARTIAL, 0 FAIL.
- Accessibility: 16 PASS, 1 PARTIAL. No WCAG certification is claimed.
- Privacy usability: 7 PASS, 0 PARTIAL, 0 FAIL.
- Findings: 2; critical 0, major 0, minor 1, cosmetic/validation gap 1.

## Findings and Fixes

- S220-F001 (severity 2): Document requests have no required fields, but the frozen mapping references one optional field, so users visit the optional-details page before review.
- S220-F002 (severity 1): Automated semantics and labelled-control checks exist, but TalkBack and VoiceOver behavior was not independently validated.

No production usability fix was applied. Neither finding is a major blocker, and changing the protected query structure or workflow was outside the minimal-fix policy.

## Targets

- 1. All four walkthrough scenarios complete exactly as specified: **PARTIAL**
- 2. No critical usability defects: **PASS**
- 3. No major blocker in the main workflow: **PASS**
- 4. All primary actions have visible labels: **PASS**
- 5. All key pages provide system feedback: **PASS**
- 6. Users can cancel or restart safely: **PASS**
- 7. Sensitive manual values are masked: **PASS**
- 8. Previous session values clear after reset: **PASS**
- 9. Banker view uses non-technical wording: **PASS**
- 10. Light and dark modes remain readable: **PASS**
- 11. Privacy messages are visible: **PASS**
- 12. Developer tools remain separated: **PASS**
- 13. No customer information is persisted: **PASS**
- 14. No overflow or crash occurs in tested screens: **PASS**

## Automated Validation

- `flutter pub get`: PASS
- `flutter analyze`: PASS
- Flutter tests: PASS (102 tests)
- Python tests: PASS (84 tests)
- Broad legacy discovery diagnostic: 111/114 passed; two superseded Sprint 2.17 hash expectations and one unavailable-TensorFlow legacy check are excluded from the current corrected v2 validation set.
- Android debug APK: PASS
- APK: `flutter_app/build/app/outputs/flutter-apk/app-debug.apk`
- APK size: 231237427 bytes
- APK SHA-256: `7674F28B651770227F3DD688876795763709316C48ABE7EDE73D8BDBB778C9E9`
- `git diff --check`: PASS

## Integrity

- Protected model and manifest hashes: PASS
- Corrected dataset: 1000 samples, 40 labels, 25 per label
- Corrected backup hash: PASS
- Frozen query content: PASS
- Android/iOS package identifiers: PASS

## Limitations and Future Work

This is a self-inspection by the developer/researcher, not independent user evidence. It does not establish user satisfaction, Deaf-user usability, banking-staff usability, WCAG conformance, or generalizable results. Future work should include independent evaluation with Deaf and hard-of-hearing users, bank staff, and assistive-technology users. Sprint 2.21 was not started.
