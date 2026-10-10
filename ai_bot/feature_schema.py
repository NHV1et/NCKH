
"""
Feature schema cho AI phát hiện website giả mạo.

Schema này phải được dùng thống nhất khi:
- Đọc dataset.
- Huấn luyện model.
- Nhận feature từ crawler.
- Chạy inference.

Lưu ý:
- Không tự động thay giá trị thiếu bằng 0.
- Không ép feature nhiều mức thành nhị phân.
"""

from collections.abc import Mapping
from math import isfinite
from numbers import Real
from typing import Any


SCHEMA_VERSION = "1.0.0"

# ============================================================
# 1. DANH SÁCH FEATURE
# Thứ tự này sẽ được dùng khi tạo đầu vào cho model.
# ============================================================

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

LABEL_COLUMN = "label"

METADATA_COLUMNS = [
    "domain",
    "url",
]


# ============================================================
# 2. PHÂN LOẠI FEATURE THEO GIÁ TRỊ ĐƯỢC PHÉP
# ============================================================

BINARY_FEATURES = [
    name
    for name in FEATURE_COLUMNS
    if name not in {
        "has_signature",
        "trusted_ssl_certificate",
    }
]

CATEGORICAL_FEATURE_VALUES = {
    # Theo hàm FeatureScraper.has_signature()
    "has_signature": {0, 1, 2},

    # Theo hàm FeatureScraper.trusted_ssl_certificate()
    # -1: không có SSL theo nhánh kiểm tra hiện tại
    #  0: issuer thuộc whitelist
    #  1: issuer khác hoặc gặp lỗi kết nối/SSL
    #  2: issuer thuộc danh sách suslist
    "trusted_ssl_certificate": {-1, 0, 1, 2},
}


# ============================================================
# 3. KIỂM TRA GIÁ TRỊ SỐ
# ============================================================

def _validate_integer_value(
    feature_name: str,
    value: Any,
) -> int:
    """Chấp nhận số nguyên hợp lệ, không chấp nhận chuỗi."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            f"Feature '{feature_name}' phải là số nguyên; "
            f"nhận được {value!r}."
        )

    if not isfinite(float(value)):
        raise ValueError(
            f"Feature '{feature_name}' không được là NaN/Inf."
        )

    if int(value) != value:
        raise ValueError(
            f"Feature '{feature_name}' phải là số nguyên; "
            f"nhận được {value!r}."
        )

    return int(value)


def validate_feature_value(
    feature_name: str,
    value: Any,
) -> int:
    """Kiểm tra một feature theo quy tắc của schema."""

    if feature_name not in FEATURE_COLUMNS:
        raise ValueError(
            f"Feature không được khai báo trong schema: "
            f"{feature_name}"
        )

    number = _validate_integer_value(feature_name, value)

    if feature_name in BINARY_FEATURES:
        if number not in (0, 1):
            raise ValueError(
                f"Feature '{feature_name}' chỉ nhận 0 hoặc 1; "
                f"nhận được {number}."
            )

    elif feature_name in CATEGORICAL_FEATURE_VALUES:
        allowed_values = CATEGORICAL_FEATURE_VALUES[feature_name]

        if number not in allowed_values:
            raise ValueError(
                f"Feature '{feature_name}' chỉ nhận một trong "
                f"{sorted(allowed_values)}; nhận được {number}."
            )

    return number


# ============================================================
# 4. KIỂM TRA VÀ CHUẨN HÓA FEATURE ĐẦU VÀO
# ============================================================

def validate_features(
    features: Mapping[str, Any],
) -> dict[str, int]:
    """
    Kiểm tra dữ liệu và trả về đúng thứ tự FEATURE_COLUMNS.

    Có thể nhận report crawler chứa thêm domain, url hoặc
    metadata. Những trường bổ sung sẽ không đưa vào model.

    Thiếu feature hoặc giá trị không hợp lệ sẽ báo lỗi.
    """

    if not isinstance(features, Mapping):
        raise TypeError(
            "features phải là dictionary hoặc Mapping."
        )

    missing = [
        name
        for name in FEATURE_COLUMNS
        if name not in features
    ]

    if missing:
        raise ValueError(
            "Thiếu feature bắt buộc: " + ", ".join(missing)
        )

    result = {}

    for name in FEATURE_COLUMNS:
        result[name] = validate_feature_value(
            name,
            features[name],
        )

    return result


def get_model_features(
    features: Mapping[str, Any],
) -> dict[str, int]:
    """Lấy và chuẩn hóa các feature được model sử dụng."""

    return validate_features(features)


# ============================================================
# 5. KIỂM TRA CỘT DATASET
# ============================================================

def validate_dataset_columns(
    columns: list[str],
    require_label: bool = True,
) -> None:
    """
    Kiểm tra header CSV/DataFrame trước khi train.

    require_label=True: yêu cầu có cột label.
    require_label=False: chỉ kiểm tra feature.
    """

    if len(columns) != len(set(columns)):
        raise ValueError("Dataset có tên cột bị trùng.")

    required = FEATURE_COLUMNS.copy()

    if require_label:
        required.append(LABEL_COLUMN)

    missing = [
        name
        for name in required
        if name not in columns
    ]

    if missing:
        raise ValueError(
            "Dataset thiếu cột bắt buộc: "
            + ", ".join(missing)
        )
