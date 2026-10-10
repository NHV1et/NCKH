from pathlib import Path
import json
import pandas as pd
from xgboost import XGBClassifier

from ai_bot.output_schema import DetectionResult
from ai_bot.explain import explain_prediction
from ai_bot.llm_client import explain_result
from ai_bot.threshold import load_threshold
from ai_bot.threshold import classify_probability

FEATURE_COLUMNS = [
    "has_ip_address_in_url",
    "has_sus_sign",
    "has_prefix",
    "has_signature",
    "has_icon",
    "long_url",
    "domain_has_https",
    "shortcut_url",
    "has_index",
    "has_sus_port",
    "has_dns_records",
    "short_domain_age",
    "short_domain_registation_length",
    "trusted_ssl_certificate",
    "disabled_right_click",
    "on_mouse_over",
    "multi_web_forward",
    "abnormal_url_anchor",
    "has_emc",
    "has_iframe_hidden",
    "has_nca",
    "high_web_rank",
    "high_domain_rating",
]


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "full_model.json"

model = XGBClassifier()
model.load_model(str(MODEL_PATH))


def predict(features: dict) -> DetectionResult:
    """Nhận features và trả về kết quả phát hiện website."""

    missing = [
        name for name in FEATURE_COLUMNS
        if name not in features
    ]

    if missing:
        raise ValueError(
            f"Thiếu features: {', '.join(missing)}"
        )

    df = pd.DataFrame([
        {name: features[name] for name in FEATURE_COLUMNS}
    ])

    for column in FEATURE_COLUMNS:
        df[column] = pd.to_numeric(
            df[column], errors="raise"
        )

    probabilities = model.predict_proba(df)[0]

    # Giả định: 0 = real, 1 = fake
    fake_probability = float(probabilities[1])

    threshold = load_threshold()

    label = classify_probability(fake_probability)

    feature_impacts = explain_prediction(
        model,
        df,
        FEATURE_COLUMNS,
        top_n=5,
    )

    reasons = []

    for item in feature_impacts:
        if item.impact > 0:
            reasons.append(
                f"{item.feature} góp phần tăng nguy cơ phishing"
            )
        elif item.impact < 0:
            reasons.append(
                f"{item.feature} góp phần giảm nguy cơ phishing"
            )

    
    result = DetectionResult(
        score=round(fake_probability * 100),
        confidence=float(max(probabilities)),
        label=label,
        reasons=reasons,
        feature_impacts=feature_impacts,
        features_used=FEATURE_COLUMNS,
        explanation=None,
        version="full_v1.0",
    )

    try:
        result.explanation = explain_result(result)
    except Exception:
        result.explanation = (
            "Không thể tạo giải thích bằng LLM. "
            "Kết quả XGBoost vẫn được giữ nguyên."
        )

    return result

if __name__ == "__main__":
    JSON_PATH = (BASE_DIR.parent / "report.json").resolve()

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        features = json.load(f)

    result = predict(features)

    print("\n" + "=" * 60)
    print("KẾT QUẢ PHÁT HIỆN")
    print("=" * 60)

    print(f"Label       : {result.label}")
    print(f"Risk Score  : {result.score}/100")
    print(f"Confidence  : {result.confidence:.2f}")

    print("\nGIẢI THÍCH:")
    print(result.explanation)

    print("=" * 60)