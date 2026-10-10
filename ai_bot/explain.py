import shap
import pandas as pd

from ai_bot.output_schema import FeatureImpact


def explain_prediction(
    model,
    df: pd.DataFrame,
    feature_columns: list[str],
    top_n: int = 5,
) -> list[FeatureImpact]:
    """
    Giải thích dự đoán XGBoost bằng SHAP.

    Args:
        model: Model XGBoost đã được huấn luyện.
        df: DataFrame chứa dữ liệu của một hoặc nhiều mẫu.
        feature_columns: Danh sách feature theo đúng thứ tự model.
        top_n: Số feature có ảnh hưởng lớn nhất cần trả về.

    Returns:
        Danh sách FeatureImpact, sắp xếp theo trị tuyệt đối của SHAP.
    """

    if df.empty:
        return []

    if top_n <= 0:
        return []

    if list(df.columns) != feature_columns:
        raise ValueError(
            "Các cột trong df phải khớp feature_columns "
            "và đúng thứ tự."
        )

    # Giải thích mẫu đầu tiên
    sample = df.iloc[[0]]

    explainer = shap.TreeExplainer(model)
    shap_result = explainer(sample)

    shap_values = shap_result.values

    # Chuẩn hóa output SHAP về một giá trị cho mỗi feature
    if shap_values.ndim == 3:
        # Dạng (samples, features, classes)
        shap_values = shap_values[0, :, 1]
    elif shap_values.ndim == 2:
        # Dạng (samples, features)
        shap_values = shap_values[0]
    else:
        raise ValueError(
            f"Shape SHAP không được hỗ trợ: {shap_values.shape}"
        )

    feature_impacts = []

    for feature, value, impact in zip(
        feature_columns,
        sample.iloc[0],
        shap_values,
    ):
        feature_impacts.append(
            FeatureImpact(
                feature=feature,
                value=float(value),
                impact=float(impact),
            )
        )

    feature_impacts.sort(
        key=lambda item: abs(item.impact),
        reverse=True,
    )

    return feature_impacts[:top_n]