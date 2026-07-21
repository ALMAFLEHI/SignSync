# Latency Summary

## Development-Machine TFLite Timing

- Float32: mean 0.1325 ms, median 0.1260 ms, P95 0.1881 ms over 100 runs after 10 warm-ups.
- Dynamic range: mean 0.0317 ms, median 0.0273 ms, P95 0.0507 ms over 100 runs after 10 warm-ups.

These are development-machine interpreter measurements, not Samsung A55 latency.

## Existing Samsung A55 Screenshot Observations

- `document`: capture 14553 ms, 4.12 FPS, feature 1 ms, TFLite 2 ms, end-to-end prediction 4 ms.
- `credit_card`: capture 16676 ms, 3.60 FPS, feature 1 ms, TFLite 2 ms, end-to-end prediction 3 ms.
- `complaint`: capture 23808 ms, 2.52 FPS, feature 2 ms, TFLite 3 ms, end-to-end prediction 5 ms.

Additional in-memory examples:

- Screenshot 1: model load 1.473 ms, feature 1.981 ms, TFLite 3.260 ms, prediction processing 5.270 ms.
- Screenshot 2: model load 1.560 ms, feature 2.471 ms, TFLite 1.360 ms, prediction processing 3.886 ms.

Only screenshot observations are available. No formal mobile mean, median, P95,
or comprehensive end-to-end latency distribution is claimed.
