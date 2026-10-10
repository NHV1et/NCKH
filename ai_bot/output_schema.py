from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FeatureImpact(BaseModel):
    """Mức độ ảnh hưởng của feature theo SHAP."""

    feature: str = Field(
        ...,
        description="Tên feature"
    )

    value: float = Field(
        ...,
        description="Giá trị feature đầu vào"
    )

    impact: float = Field(
        ...,
        description=(
            "Giá trị SHAP của feature. "
            "Dấu và độ lớn được diễn giải theo output mà SHAP giải thích."
        )
    )


class DetectionResult(BaseModel):
    """Kết quả phát hiện website phishing."""

    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Điểm rủi ro phishing, từ 0 đến 100"
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Độ tin cậy theo quy ước của hệ thống, từ 0 đến 1"
    )

    label: Literal["real", "suspicious", "phishing"] = Field(
        ...,
        description="Nhãn dự đoán của model"
    )

    reasons: List[str] = Field(
        default_factory=list,
        description="Các dấu hiệu chính hỗ trợ kết quả dự đoán"
    )

    feature_impacts: List[FeatureImpact] = Field(
        default_factory=list,
        description="Danh sách feature và mức độ ảnh hưởng theo SHAP"
    )

    features_used: List[str] = Field(
        default_factory=list,
        description="Danh sách feature đầu vào model đã sử dụng"
    )

    explanation: Optional[str] = Field(
        default=None,
        description="Giải thích kết quả bằng ngôn ngữ tự nhiên từ LLM"
    )

    version: str = Field(
        default="full_v1.0",
        description="Phiên bản model"
    )