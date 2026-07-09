# Sprint 2.16A Live Retest Report

## Result

PENDING

## Reason

Live retesting after model update cannot happen until phone samples are recorded, pulled, validated, mixed into the dataset, retrained, converted to TFLite, and copied into Flutter.

## Before Sprint 2.16A Weak Labels

From Sprint 2.15 limited Samsung phone testing:

- `transfer`: failed 3 attempts, often predicted `Z`
- `address_change`: mixed result, sometimes predicted `transfer` around 97% confidence
- `document`: failed
- `signature`: mixed result
- `atm`: failed

## Retest Plan

After an updated TFLite model exists, test each weak label at least 3 times:

- true label
- predicted label
- confidence
- correct or wrong
- whether Try Again appeared
- whether stabilized prediction helped

Also retest strong labels:

- `A`
- `7`
- `deposit`
- `payment`
- `balance`

## Scope Note

No live retest result is claimed in this setup commit.
