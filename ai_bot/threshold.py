
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_thresholds() -> tuple[float, float]:
    """Đọc hai ngưỡng phân loại từ config.yaml."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file cấu hình: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    decision = config.get("decision", {})

    low = float(decision.get("low_threshold", 0.27))
    high = float(decision.get("high_threshold", 0.93))

    if not 0 < low < high < 1:
        raise ValueError(
            "Cần thỏa mãn: 0 < low_threshold < high_threshold < 1"
        )

    return low, high


def classify_probability(
    fake_probability: float,
    low_threshold: float | None = None,
    high_threshold: float | None = None,
) -> str:
    """
    Phân loại dựa trên xác suất phishing.

    fake_probability: xác suất thuộc lớp phishing, từ 0 đến 1.
    """

    if not 0 <= fake_probability <= 1:
        raise ValueError(
            "fake_probability phải nằm trong khoảng [0, 1]"
        )

    if low_threshold is None or high_threshold is None:
        config_low, config_high = load_thresholds()

        if low_threshold is None:
            low_threshold = config_low

        if high_threshold is None:
            high_threshold = config_high

    if not 0 < low_threshold < high_threshold < 1:
        raise ValueError(
            "Cần thỏa mãn: 0 < low_threshold < high_threshold < 1"
        )

    if fake_probability < low_threshold:
        return "real"
    elif fake_probability < high_threshold:
        return "suspicious"
    else:
        return "phishing"
