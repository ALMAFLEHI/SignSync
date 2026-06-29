"""Check TensorFlow/TFLite prerequisites for Sprint 2.13 without crashing."""

from __future__ import annotations

import importlib
import platform
import sys

from tflite_model_config import (
    ENVIRONMENT_CHECK_MD_PATH,
    SOURCE_DATASET_PATH,
    SOURCE_LABEL_GROUPS_PATH,
    SOURCE_LABEL_MAPPING_PATH,
)


def check_tensorflow() -> dict[str, object]:
    """Import TensorFlow if available and report converter support."""
    result: dict[str, object] = {
        "available": False,
        "version": "",
        "converter_available": False,
        "error": "",
    }
    try:
        tensorflow = importlib.import_module("tensorflow")
    except Exception as exc:  # noqa: BLE001 - environment report should not crash.
        result["error"] = str(exc)
        return result

    result["available"] = True
    result["version"] = getattr(tensorflow, "__version__", "unknown")
    result["converter_available"] = hasattr(getattr(tensorflow, "lite", None), "TFLiteConverter")
    return result


def write_report(tf_result: dict[str, object], dataset_ready: bool, mapping_ready: bool, groups_ready: bool) -> None:
    """Write a concise Markdown evidence report for the environment check."""
    ENVIRONMENT_CHECK_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = (
        "PASS"
        if tf_result["available"] and tf_result["converter_available"] and dataset_ready and mapping_ready and groups_ready
        else "ENVIRONMENT_PENDING"
    )
    guidance = "" if status == "PASS" else """
## Installation Guidance

TensorFlow is not ready in this Python environment. Use a compatible Python 3.11/3.12 virtual environment, WSL, or Google Colab, then run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements_sprint_2_13.txt
python ml/src/check_tflite_environment.py
```
"""
    content = f"""# Sprint 2.13 TensorFlow/TFLite Environment Check

## Result
{status}

## Python
- Executable: {sys.executable}
- Version: {platform.python_version()}
- Platform: {platform.platform()}

## TensorFlow
- Imports: {tf_result['available']}
- Version: {tf_result['version'] or 'not available'}
- TFLiteConverter available: {tf_result['converter_available']}
- Error: {tf_result['error'] or 'None'}

## Dataset Prerequisites
- Expanded dataset exists: {dataset_ready}
- Label mapping exists: {mapping_ready}
- Label groups exists: {groups_ready}
{guidance}
"""
    ENVIRONMENT_CHECK_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Print TensorFlow and dataset readiness for Sprint 2.13."""
    tf_result = check_tensorflow()
    dataset_ready = SOURCE_DATASET_PATH.exists()
    mapping_ready = SOURCE_LABEL_MAPPING_PATH.exists()
    groups_ready = SOURCE_LABEL_GROUPS_PATH.exists()
    passed = (
        bool(tf_result["available"])
        and bool(tf_result["converter_available"])
        and dataset_ready
        and mapping_ready
        and groups_ready
    )
    write_report(tf_result, dataset_ready, mapping_ready, groups_ready)

    print("Sprint 2.13 TensorFlow/TFLite Environment Check")
    print("------------------------------------------------")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {platform.python_version()}")
    print(f"TensorFlow imports: {tf_result['available']}")
    print(f"TensorFlow version: {tf_result['version'] or 'not available'}")
    print(f"TFLiteConverter available: {tf_result['converter_available']}")
    print(f"expanded dataset exists: {dataset_ready}")
    print(f"label mapping exists: {mapping_ready}")
    print(f"label groups exists: {groups_ready}")
    print(f"report: {ENVIRONMENT_CHECK_MD_PATH.as_posix()}")
    if passed:
        print("PASS: TensorFlow/TFLite environment is ready.")
        return 0
    print("ENVIRONMENT_PENDING: TensorFlow/TFLite is not ready in this environment.")
    print("Use a compatible Python environment and install requirements_sprint_2_13.txt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
