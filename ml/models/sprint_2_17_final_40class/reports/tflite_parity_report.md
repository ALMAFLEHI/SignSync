# Sprint 2.17 Keras-TFLite Parity and Runtime Report

## Contract

Both TFLite candidates load with a float32 `[1, 756]` input and float32 `[1, 40]` output. The output order is the frozen 40-intent metadata order; it contains no alphabet, digit, or removed-label classes.

## Parity

- Samples: 40 (one locked test sample per class, prioritizing errors and low confidence)
- Keras to float32 TFLite top-1 agreement: 1.0000
- Keras to dynamic-range TFLite top-1 agreement: 1.0000
- Float32 maximum absolute probability difference: 0.00000060
- Dynamic maximum absolute probability difference: 0.01616341

The parity run verifies conversion consistency and does not alter the already closed aggregate test evaluation.

## Sizes

- Keras: 6734168 bytes
- Float32 TFLite: 2237236 bytes
- Dynamic-range TFLite: 580536 bytes

## Development-Machine Latency

| Model | Warm-up | Runs | Mean ms | Median ms | P95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Float32 TFLite | 10 | 100 | 0.113 | 0.106 | 0.172 |
| Dynamic-range TFLite | 10 | 100 | 0.020 | 0.018 | 0.029 |

These measurements are desktop development-machine interpreter latency, not Samsung Galaxy A55 mobile latency. The candidate remains `candidate_not_deployed`.
