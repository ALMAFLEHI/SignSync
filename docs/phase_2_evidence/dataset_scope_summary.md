# SignSync Dataset Scope Summary

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.1: Project Setup & Dataset Scope

## Label Counts
- Total labels: 56
- Alphabet labels: 26
- Digit labels: 10
- Banking intent labels: 20

## Full Banking Intent List
- deposit
- withdraw
- balance
- transfer
- account
- card
- pin
- password
- identity_verification
- cash
- receipt
- fee
- loan
- savings
- open_account
- close_account
- fraud
- block_card
- help
- confirm

## Folder Structure Summary
- ml/data_raw/videos
- ml/data_processed/landmarks
- ml/models
- ml/reports
- ml/src
- flutter_app
- docs/phase_2_evidence
- ml/metadata.csv
- Label subfolders under ml/data_raw/videos
- Label subfolders under ml/data_processed/landmarks

## Acceptance Checklist
- [x] Main project folders are created.
- [x] Raw video label folders are created for all labels.
- [x] Processed landmark label folders are created for all labels.
- [x] metadata.csv exists with the required headers.
- [x] Initial dataset vocabulary contains 56 unique labels.
- [x] No data collection, landmark extraction, or model training is included in this sprint.
