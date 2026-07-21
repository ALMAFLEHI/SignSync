"""Frozen configuration for Sprint 2.19 live technical evaluation."""

from __future__ import annotations

from pathlib import Path

from labels import BANKING_INTENTS_V3_40


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_VERSION = "sprint_2_19_live_evaluation_v1"
RANDOM_SEED = 21919
BLOCK_COUNT = 10
TRIALS_PER_BLOCK = 40
EXPECTED_TRIALS = BLOCK_COUNT * TRIALS_PER_BLOCK
STANDARD_BLOCKS = frozenset(range(1, 6))
VARIATION_BLOCKS = frozenset(range(6, 11))
STANDARD_CONDITION = "standard"
VARIATION_CONDITION = "mild_variation"
WARM_UP_TRIALS = 5
CONFIDENCE_THRESHOLD = 0.80
MINIMUM_MARGIN = 0.00
SCHEDULE_SHA256 = (
    "57E858AB6D6AB0C978BAD3E6A73EB2E08BC7531CE5F766AD82953B3FA558CB76"
)
MODEL_VERSION = "signsync_40class_account_corrected_v2"
ANDROID_PACKAGE_ID = "com.example.flutter_app"
PRIMARY_DEVICE_MODEL = "SM-A556E"
WEAK_CLASSES = ["loan", "card", "payment", "document", "help"]
FINAL_LABELS = list(BANKING_INTENTS_V3_40)
DYNAMIC_MODEL_SHA256 = (
    "BD46131FF20ECB96F240C867C60804A2D9F514AC4F56D63F64E8B60188187A17"
)
FLOAT32_MODEL_SHA256 = (
    "D9686110BACFB1F1C5B3BFBF33B2C515393344869A3DCEAFF325903A34DF278C"
)
LABELS_SHA256 = (
    "CF8BE5AD57C57A3EDA1029010FA7A5D9663F226294661A869CED375E0236E286"
)
DEPLOYMENT_MANIFEST_SHA256 = (
    "F02E35864C87925A6D06D70F669411388B2F04112F757CB0DF2AAD1296A2F9F1"
)
CORRECTED_DATASET_MANIFEST_SHA256 = (
    "677C4ED15F11CE4BEE07754948CCEB21E324BDC1C3481CF265E884F773710D03"
)
CORRECTED_BACKUP_SHA256 = (
    "07B5660E08640EA2EAC11216E41F4696D01BE52627CF3E1DD15D46F99C20286A"
)

DOC_SCHEDULE = (
    ROOT / "docs" / "phase_2_evidence" / "sprint_2_19_trial_schedule.csv"
)
FLUTTER_SCHEDULE = (
    ROOT
    / "flutter_app"
    / "assets"
    / "evaluation"
    / "sprint_2_19_trial_schedule.csv"
)
REPORT_ROOT = ROOT / "ml" / "reports" / "sprint_2_19_final_technical_evaluation"
RAW_EXPORTS_DIR = REPORT_ROOT / "raw_exports"
VALIDATED_DIR = REPORT_ROOT / "validated"
METRICS_DIR = REPORT_ROOT / "metrics"
CONFUSION_DIR = REPORT_ROOT / "confusion"
FIGURES_DIR = REPORT_ROOT / "figures"
REPORTS_DIR = REPORT_ROOT / "reports"
METADATA_DIR = REPORT_ROOT / "metadata"

TRIAL_COLUMNS = [
    "protocol_version",
    "session_id",
    "trial_number",
    "block_number",
    "condition",
    "intended_label",
    "intended_label_index",
    "predicted_label",
    "predicted_label_index",
    "confidence",
    "second_label",
    "second_confidence",
    "confidence_margin",
    "accepted",
    "rejected",
    "correct_top1",
    "correct_and_accepted",
    "incorrect_and_accepted",
    "correct_but_rejected",
    "capture_duration_ms",
    "average_capture_fps",
    "feature_computation_ms",
    "tflite_inference_ms",
    "prediction_processing_ms",
    "model_load_ms",
    "technical_status",
    "device_model",
    "android_version",
    "active_model_version",
    "active_model_sha256",
    "confidence_threshold",
    "timestamp",
    "notes",
]

TECHNICAL_EVENT_COLUMNS = [
    "session_id",
    "event_number",
    "trial_number",
    "block_number",
    "condition",
    "intended_label",
    "event_type",
    "message",
    "timestamp",
]

FORBIDDEN_EXPORT_TERMS = {
    "image",
    "video",
    "frame",
    "landmark",
    "feature",
    "account_number",
    "customer_name",
    "banking_detail",
    "query_selection",
    "audio",
    "location",
}


def ensure_output_directories() -> None:
    """Create the planned report structure without generating physical results."""
    for path in (
        RAW_EXPORTS_DIR,
        VALIDATED_DIR,
        METRICS_DIR,
        CONFUSION_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        METADATA_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def validate_config() -> None:
    """Protect the final class order and 400-trial design."""
    if len(FINAL_LABELS) != 40 or len(set(FINAL_LABELS)) != 40:
        raise ValueError("Sprint 2.19 requires exactly 40 unique labels.")
    if FINAL_LABELS[4] != "account" or FINAL_LABELS[13] != "savings":
        raise ValueError("Account or savings index changed.")
    if EXPECTED_TRIALS != 400 or WARM_UP_TRIALS != 5:
        raise ValueError("Sprint 2.19 trial or warm-up count changed.")
    if CONFIDENCE_THRESHOLD != 0.80 or MINIMUM_MARGIN != 0.00:
        raise ValueError("The frozen confidence policy changed.")


validate_config()
