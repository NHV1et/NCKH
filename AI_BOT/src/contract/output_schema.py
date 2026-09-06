from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class FeatureImpact(BaseModel):
    """
    Thông tin mức độ ảnh hưởng của một feature theo SHAP.
    """

    feature: str = Field(
        ...,
        description="Tên feature"
    )

    value: float = Field(
        ...,
        description="Giá trị của feature"
    )

    impact: float = Field(
        ...,
        description=(
            "Giá trị SHAP. "
            "Dương: đẩy kết quả về phishing. "
            "Âm: đẩy kết quả về real."
        )
    )


class DetectionResult(BaseModel):
    """
    Output schema chung cho các stage:
    Fast / Medium / Full
    """

    # ============================================================
    # Thông tin stage
    # ============================================================

    stage: str = Field(
        ...,
        description="Stage thực hiện phát hiện: fast, medium hoặc full"
    )

    # ============================================================
    # Kết quả phát hiện
    # ============================================================

    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Điểm rủi ro từ 0 đến 100"
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Độ tin cậy của mô hình, từ 0 đến 1"
    )

    label: Literal["real", "phishing"] = Field(
        ...,
        description="Nhãn kết quả"
    )

    # ============================================================
    # Điều khiển pipeline
    # ============================================================

    stop: bool = Field(
        ...,
        description=(
            "True nếu kết quả đủ chắc chắn và dừng pipeline. "
            "False nếu cần chuyển sang stage tiếp theo."
        )
    )

    # ============================================================
    # Giải thích
    # ============================================================

    reasons: List[str] = Field(
        default_factory=list,
        description="Các lý do dẫn đến kết quả"
    )

    # ============================================================
    # SHAP feature impacts
    # ============================================================

    feature_impacts: List[FeatureImpact] = Field(
        default_factory=list,
        description="Mức độ ảnh hưởng của các feature theo SHAP"
    )

    # ============================================================
    # Feature được sử dụng
    # ============================================================

    features_used: List[str] = Field(
        default_factory=list,
        description="Danh sách feature được sử dụng ở stage này"
    )

    # ============================================================
    # LLM explanation
    # ============================================================

    explanation: Optional[str] = Field(
        default=None,
        description="Giải thích kết quả bằng ngôn ngữ tự nhiên từ LLM"
    )

    # ============================================================
    # Version
    # ============================================================

    version: str = Field(
        ...,
        description="Phiên bản của model/stage"
    )