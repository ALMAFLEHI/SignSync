# Sprint 2.21 Final Project Status

## What Was Built

SignSync is a Flutter/Android academic prototype that recognizes one of 40 isolated ASL banking intents on-device, asks the user to confirm the intent, offers four related local requests, accepts optional manual details, provides review, and presents a banker-readable request.

## Problem and Scope

It addresses a communication barrier for Deaf and hard-of-hearing customers during structured banking-service interactions. It is assistance software, not a transaction, authentication, or bank-integration system.

## Technical Result

The corrected final model uses 1,000 active Samsung phone landmark samples, 25 per intent. The locked 200-sample held-out test achieved 95.50% accuracy and 95.42% macro F1. Confidence coverage at 0.80 was 97.50%, with 97.95% accepted accuracy. Account and savings had no direct confusion.

## Validation

Flutter analysis and 108 tests passed. Ninety-two current authoritative Python tests passed. Debug and release-mode APKs built. The release-mode APK installed safely and launched on a Samsung SM-A556E running Android 16. Privacy, offline behavior, permissions, workflow regression, traceability, protected hashes, archives, and checksums were validated.

## Conclusion

The project is ready as an academic FYP prototype and demonstration release candidate. It is not a production banking system and must not be represented as one.
