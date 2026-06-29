# Sprint 2.13 TFLite Test Report

## Result
PASS

## Model Comparison
- keras: evaluated, accuracy 0.9254658385093167, macro F1 0.8941860465116279, weighted F1 0.9086956521739131
- tflite_float32: evaluated, accuracy 0.9254658385093167, macro F1 0.8941860465116279, weighted F1 0.9086956521739131
- tflite_dynamic_range: evaluated, accuracy 0.9254658385093167, macro F1 0.8941860465116279, weighted F1 0.9086956521739131

## Pass Rule
TFLite accuracy should be within 0.02 of the Keras model accuracy.
