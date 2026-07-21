# Corrected Held-Out Error and Weak-Class Analysis

## Observed

Lowest classes by F1: `card` (0.5455, support 5), `help` (0.7500, support 5), `loan` (0.7500, support 5), `document` (0.8889, support 5), `payment` (0.8889, support 5), `withdraw` (0.8889, support 5), `block_card` (0.9091, support 5), `cash` (0.9091, support 5).

Directional confusion pairs:

- `card` -> `cash`: 1
- `card` -> `replace_card`: 1
- `document` -> `card`: 1
- `help` -> `block_card`: 1
- `help` -> `card`: 1
- `loan` -> `pin`: 1
- `loan` -> `reset_password`: 1
- `payment` -> `card`: 1
- `withdraw` -> `password`: 1

High-confidence incorrect predictions at the frozen threshold: 4.

## Likely

Similar hand shapes, motion boundaries, signer variation, and limited real
training coverage may contribute to errors. These are plausible explanations,
not causal findings.

## Requires Further Investigation

Multi-participant evaluation, repeated live trials, and larger per-class test
support are required to determine how stable these weaknesses are. The existing
A55 smoke test does not provide class-wise error frequencies.
