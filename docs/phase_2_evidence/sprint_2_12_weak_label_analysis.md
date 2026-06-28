# Sprint 2.12 Weak Label Analysis

## Summary
- Test accuracy: 0.9441
- Weak or confusing labels found: 9
- Recommendation: Sprint 2.13 may be skipped or kept optional if the listed weak labels are acceptable.

## Weak Or Confusing Labels
- E: low F1; low recall; confused with J
- H: low F1
- N: low F1; low recall; confused with M
- V: low F1; low recall; confused with U
- 3: low F1; low recall; confused with H
- account: low F1; low recall; confused with savings
- block_card: low F1; low recall; confused with replace_card
- help: low F1; low recall; confused with signature
- confirm: low F1; low recall; confused with email_address

## Scope Boundary
This script analyzes evaluation outputs only. It does not record data, extract landmarks, train models, or modify raw videos.

## Output Files
- CSV report: docs/phase_2_evidence/sprint_2_12_weak_label_analysis.csv
- Markdown report: docs/phase_2_evidence/sprint_2_12_weak_label_analysis.md
