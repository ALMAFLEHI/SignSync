# Samsung Galaxy A55 Smoke-Test Summary

## Evidence Classification

This is deployment and coverage smoke evidence, not a formal live-device
statistical accuracy study. The user confirmed that all 40 corrected banking
intents were smoke-tested on the Samsung Galaxy A55. No complete recorded CSV
exists from which formal live accuracy can be calculated.

## Confirmed Scope

- Corrected dynamic-range TFLite model loaded on the Samsung Galaxy A55.
- Contract `[1,756] -> [1,40]` passed and threshold 0.80 was displayed.
- All 40 intents received manual smoke coverage.
- Corrected `account` and `savings` were manually verified as separate signs.
- Guided query flow, manual details, and banker-readable result worked.
- Representative screenshots show account, document, credit-card, and complaint results.
- On-device diagnostics worked; camera data and inference stayed local.

No attempt counts, formal accuracy, failure rate, or confidence distribution is
claimed from this smoke test.
