from pathlib import Path

import pandas as pd
from xgboost import XGBClassifier

from src.contract.output_schema import DetectionResult
from src.full_model.explain import explain_prediction
from src.llm.llm_client import explain_result
FEATURE_COLUMNS = [
    "Have_IP",
    "Have_At",
    "URL_Length",
    "URL_Depth",
    "Redirection",
    "https_Domain",
    "Tiny_URL",
    "Prefix/Suffix",
    "DNS_Record",
    "Web_Traffic",
    "Domain_Age",
    "Domain_End",
    "iFrame",
    "Mouse_Over",
    "Right_Click",
    "Web_Forwards"
]


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "full_model.json"

model = XGBClassifier()
model.load_model(MODEL_PATH)


def predict(features):

    df = pd.DataFrame([features])[FEATURE_COLUMNS]

    probability = model.predict_proba(df)[0]

    phishing_probability = probability[1]

    label = (
        "phishing"
        if phishing_probability >= 0.5
        else "real"
    )

    # SHAP
    feature_impacts = explain_prediction(
        model,
        df,
        FEATURE_COLUMNS,
        top_n=5
    )

    # Reasons
    reasons = []

    for item in feature_impacts:

        if item.impact > 0:
            reasons.append(
                f"{item.feature} làm tăng nguy cơ phishing"
            )
        else:
            reasons.append(
                f"{item.feature} làm giảm nguy cơ phishing"
            )

    result = DetectionResult(
        stage="full",

        score=round(
            phishing_probability * 100
        ),

        confidence=float(
            max(probability)
        ),

        label=label,

        stop=True,

        reasons=reasons,

        feature_impacts=feature_impacts,

        features_used=FEATURE_COLUMNS,

        explanation=None,

        version="full_v1.0"
    )

    # LLM giải thích
    result.explanation = explain_result(result)


    return result


# ============================================================
# TEST - Web fake
# ============================================================

features = {
    "Have_IP": 0,
    "Have_At": 1,
    "URL_Length": 1,
    "URL_Depth": 1,
    "Redirection": 1,
    "https_Domain": 0,
    "Tiny_URL": 1,
    "Prefix/Suffix": 1,
    "DNS_Record": 0,
    "Web_Traffic": 0,
    "Domain_Age": 0,
    "Domain_End": 0,
    "iFrame": 1,
    "Mouse_Over": 1,
    "Right_Click": 0,
    "Web_Forwards": 1
}


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

