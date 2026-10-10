from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_threshold() -> float:
    """Đọc ngưỡng phân loại từ config.yaml."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file cấu hình: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    threshold = float(
        config.get("decision", {}).get("threshold", 0.5)
    )

    if not 0 < threshold < 1:
        raise ValueError(
            "decision.threshold phải nằm trong khoảng (0, 1)"
        )

    return threshold


def classify_probability(
    fake_probability: float,
    threshold: float | None = None,
) -> str:
    """
    Phân loại dựa trên xác suất fake.

    fake_probability: xác suất thuộc lớp fake, từ 0 đến 1.
    threshold: ngưỡng phân loại; nếu None thì đọc từ config.
    """

    if not 0 <= fake_probability <= 1:
        raise ValueError(
            "fake_probability phải nằm trong khoảng [0, 1]"
        )

    if threshold is None:
        threshold = load_threshold()

    if not 0 < threshold < 1:
        raise ValueError(
            "threshold phải nằm trong khoảng (0, 1)"
        )

    return (
        "phishing"
        if fake_probability >= threshold
        else "real"
    )