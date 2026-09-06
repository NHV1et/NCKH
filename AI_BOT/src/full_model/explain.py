import shap
import pandas as pd

from src.contract.output_schema import FeatureImpact


def explain_prediction(model, df, feature_columns, top_n=5):
    """
    Phân tích mức độ ảnh hưởng của từng feature bằng SHAP.
    """

    explainer = shap.TreeExplainer(model)

    shap_result = explainer(df)

    shap_values = shap_result.values[0]

    feature_impacts = []

    for feature, value, impact in zip(
        feature_columns,
        df.iloc[0],
        shap_values
    ):
        feature_impacts.append(
            FeatureImpact(
                feature=feature,
                value=float(value),
                impact=float(impact)
            )
        )

    # Feature ảnh hưởng mạnh nhất
    feature_impacts.sort(
        key=lambda x: abs(x.impact),
        reverse=True
    )

    return feature_impacts[:top_n]