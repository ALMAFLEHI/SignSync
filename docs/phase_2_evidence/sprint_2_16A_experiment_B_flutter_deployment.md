# Sprint 2.16A Experiment B Flutter Deployment

## Deployment Status

PASS. The reviewed Experiment B assets are deployed and validated for controlled live Samsung Galaxy A55 testing. Live testing is still pending, Sprint 2.16A is not complete, and Sprint 2.16B remains blocked.

## Selected Model

Primary source: `ml/models/sprint_2_16A_v3_40/with_augmentation/model_dynamic_range.tflite`

The dynamic-range model was selected because it passed independent loading and Keras parity checks, uses float32 `[1, 756]` input and float32 `[1, 76]` output, and is 585,720 bytes. It preserves the same runtime contract as the 2,255,812-byte float model while reducing mobile package size. The verified float model is deployed as the existing fallback asset.

## Matching Source Metadata

- `labels.txt`
- `label_mapping.json`
- `label_groups.json`
- `preprocessing_config.json`
- `tflite_verification.json`
- Active scope: `ml/config/signsync_active_scope_v3_40.json`

## Flutter Destinations

- `flutter_app/assets/models/model_dynamic_range.tflite`
- `flutter_app/assets/models/model_float32.tflite`
- `flutter_app/assets/metadata/labels.txt`
- `flutter_app/assets/metadata/label_mapping.json`
- `flutter_app/assets/metadata/label_groups.json`
- `flutter_app/assets/metadata/preprocessing_config.json`
- `flutter_app/assets/metadata/tflite_model_metadata.json`

## Rollback Backup

Location: `flutter_app/assets/model_backups/pre_sprint_2_16A_experiment_B/`

The backup was created before replacement and was not overwritten. Its `backup_manifest.json` records source path, backup path, size, and SHA-256 for all six previous assets.

## Old And New Contracts

| Property | Previous Flutter model | Experiment B deployment |
| --- | --- | --- |
| Primary model | Sprint 2.13 dynamic range | Sprint 2.16A Experiment B dynamic range |
| Input | float32 `[1, 756]` | float32 `[1, 756]` |
| Output | float32 `[1, 86]` | float32 `[1, 76]` |
| Label count | 86 | 76 |
| Alphabet Mode | 26 | 26 |
| Number Mode | 10 | 10 |
| Banking Intent Mode | active filtering over historical outputs | exactly 40 active outputs |

## Asset Hashes

| Asset | Previous SHA-256 | Deployed SHA-256 |
| --- | --- | --- |
| Dynamic-range TFLite | `4f38bce87be60e8f5486a6aa0f14858a8ea7358c655c5f0b7f8be52cc4fcd8ec` | `88cdc0367f40e50081e5bde7644ede242937061843cb68ea1235214e62308ddd` |
| Float32 TFLite | `471da2a81cdfa6c20468f16f9291af9b246fbebc8da0f520a77439d738b70068` | `36ec44e5ebefd1c7de56161a305324488bfd6cfc58337ca9b2679198f424fac8` |
| Labels | `c9c831d3188e26268e6740bd7ac9c7f2b2ee0c2d66cb7146c03d068464128031` | `9e710a861af68e88f1b1caf0b8499789a017bbd6ca676a99d6c188ef26aa609e` |
| Label mapping | `8c9ebcc8b1fb62b260887af3ce256f25b04dfe21ae137e0560943502b959ae3c` | `7fc92ebe04c2dfad1ef997b145fb777093ca850e693e4f7b8d3006ed0d7ccaad` |
| Label groups | `dc48785b225eb610c44652d7fcec1abb54b99bce7ffdd6f232bb25bcb25eae9b` | `8a1236765a782a2bc69ca3c473f8c93d7dc9971f8d0161337687dbb7084f7ec4` |
| Model metadata | `71ac0f6cb3f408c87bc68a7fb384cdbdbf750faebddf8f1fcdcb0fb66fb5b12d` | `ade2b09ce6aad742b904ebbb06364560599c96b88d4249e72a82acefa06d5f1c` |
| Preprocessing config | not a separate old asset | `a0d01659aecd0798d6ce929a304e22044672b203eaa8d0b31c475834faffb4d6` |

## Runtime Behaviour Preserved

- Feature order remains mean, population standard deviation, minimum, maximum, first frame, last frame.
- Sequence and hand-slot contract remains 60x126, left indices 0-62, right indices 63-125, missing hand represented by zeros.
- Raw top predictions remain available for debugging.
- Banking confidence threshold remains 0.70.
- Minimum top-two gap remains 0.15.
- Low-confidence or ambiguous captures display `Try Again`.
- Three-capture stabilization remains enabled with two agreeing captures required.
- The 10 removed banking labels are absent from labels, mappings, and all final mode outputs.

## Validation Executed

- Python syntax compilation: PASS.
- Deployment source and backup validation: PASS.
- Old TFLite contract `[1, 756]` to `[1, 86]`: PASS.
- Both deployed TFLite contracts `[1, 756]` to `[1, 76]`: PASS.
- Float32 input/output dtype verification: PASS.
- Deployed/source SHA-256 equality: PASS.
- Four deterministic Experiment B TFLite fixtures: PASS.
- Phone feature parity max absolute difference: `2.38418579e-07`, PASS.
- Active V3 scope check: PASS.
- Detailed 100-sample phone validation: PASS.
- Controlled experiment audit, 243 checks: PASS.
- Dart formatting check: PASS, zero files changed.
- Flutter dependency resolution: PASS.
- Flutter analysis: PASS, no issues.
- Flutter tests: PASS, 24 tests.
- Android debug APK build: PASS.
- APK asset inspection: PASS; both models and all matching metadata files are packaged.
- `git diff --check`: PASS; only expected Windows LF-to-CRLF notices were reported.

## Limitations And Boundary

The deployment proves packaging, model loading through a TFLite interpreter, tensor compatibility, metadata correctness, deterministic offline inference, and Android build compatibility. It does not prove live camera accuracy. The 65 fresh A55 attempts must be recorded manually without reusing saved phone data. No retraining, dataset modification, commit, push, or Sprint 2.16B work was performed.
