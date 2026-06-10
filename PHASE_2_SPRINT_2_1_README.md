# Phase 2 Sprint 2.1 README

## What This Sprint Does
Sprint 2.1 sets up the initial SignSync machine learning project structure and defines the first dataset vocabulary for the FYP. It creates safe, repeatable folders for raw videos and processed landmark outputs, initializes `metadata.csv`, and writes a dataset scope summary for documentation evidence.

This sprint does not include data collection, landmark extraction, model training, or Flutter implementation.

## How To Run The Setup Script
From the project root, run:

```powershell
python ml/src/create_folders.py
```

The script is safe to run multiple times. It creates missing folders, keeps existing folders, and only creates `ml/metadata.csv` if it does not already exist.

## Expected Files And Folders
After running the setup script, the project should contain:

```text
signsync/
├── ml/
│   ├── metadata.csv
│   ├── data_raw/
│   │   └── videos/
│   │       └── [one folder per label]
│   ├── data_processed/
│   │   └── landmarks/
│   │       └── [one folder per label]
│   ├── models/
│   ├── reports/
│   └── src/
│       ├── create_folders.py
│       └── labels.py
├── flutter_app/
├── docs/
│   └── phase_2_evidence/
│       └── dataset_scope_summary.md
└── PHASE_2_SPRINT_2_1_README.md
```

## FYP Evidence Screenshots
Save screenshots of:

- The terminal output showing validation passed and the Sprint 2.1 summary.
- The `ml/data_raw/videos` folder showing label subfolders.
- The `ml/data_processed/landmarks` folder showing label subfolders.
- The `ml/metadata.csv` file showing the required headers.
- The `docs/phase_2_evidence/dataset_scope_summary.md` file.
