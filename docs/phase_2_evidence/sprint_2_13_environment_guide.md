# Sprint 2.13 TensorFlow/TFLite Environment Guide

## Purpose

Sprint 2.13 adds a TensorFlow/Keras training and TensorFlow Lite export path for the completed SignSync expanded V2 dataset. The existing scikit-learn ExtraTrees model remains useful for controlled accuracy reporting, but it is not the safest direct path for Flutter/TFLite deployment.

## Python Version Notes

TensorFlow package compatibility depends on the TensorFlow release and operating system. The official TensorFlow pip installation guide is the primary reference:

- https://www.tensorflow.org/install/pip

Use a TensorFlow-supported Python version for training and conversion. A practical local setup for this project is Python 3.11 or Python 3.12 in a virtual environment. If a newer local Python version is installed and TensorFlow does not support it, create a separate compatible environment rather than changing the existing project files.

## Current Environment Detection

Run:

```powershell
python ml/src/check_tflite_environment.py
```

The script reports:

- Python executable
- Python version
- whether TensorFlow imports
- TensorFlow version when available
- whether `tf.lite.TFLiteConverter` is available
- whether the expanded V2 dataset and label metadata exist

## Recommended Local Setup

Create a separate environment, then install Sprint 2.13 requirements:

```powershell
py -3.11 -m venv .venv-tflite
.\.venv-tflite\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements_sprint_2_13.txt
python ml/src/check_tflite_environment.py
```

If `tensorflow-cpu` is not available for the local Python version, use a compatible Python 3.11/3.12 environment, WSL, or Google Colab for Keras training and TFLite conversion.

## Safety Boundary

Do not install packages globally without confirmation. Do not replace the Sprint 2.12 scikit-learn model. Sprint 2.13 writes only to new Sprint 2.13 paths.
