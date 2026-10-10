
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from ai_bot.feature_schema import (
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    validate_dataset_columns,
    validate_feature_value,
)


def load_dataset(
    fake_path="ai_bot/data/fake.csv",
    real_path="ai_bot/data/real.csv",
    test_size=0.2,
    random_state=42,
):
    """Đọc, kiểm tra và gộp hai dataset fake/real."""

    # 1. Kiểm tra đường dẫn
    fake_path = Path(fake_path)
    real_path = Path(real_path)

    for path in (fake_path, real_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy dataset: {path}"
            )

    # 2. Đọc dữ liệu
    fake_df = pd.read_csv(fake_path)
    real_df = pd.read_csv(real_path)

    # Chuẩn hóa tên cột nhãn nếu dùng định dạng cũ
    fake_df = fake_df.rename(columns={"Label": "label"})
    real_df = real_df.rename(columns={"Label": "label"})

    # 3. Kiểm tra schema
    validate_dataset_columns(
        list(fake_df.columns),
        require_label=True,
    )
    validate_dataset_columns(
        list(real_df.columns),
        require_label=True,
    )

    if set(fake_df.columns) != set(real_df.columns):
        raise ValueError(
            "fake.csv và real.csv có cấu trúc cột khác nhau."
        )

    # 4. Gộp dữ liệu theo đúng thứ tự feature
    df = pd.concat(
        [fake_df, real_df],
        ignore_index=True,
    )

    df = df[FEATURE_COLUMNS + [LABEL_COLUMN]]

    # 5. Kiểm tra nhãn
    if df[LABEL_COLUMN].isnull().any():
        raise ValueError("Dataset có label bị thiếu.")

    labels = set(df[LABEL_COLUMN].unique())

    if not labels.issubset({0, 1}):
        raise ValueError(
            f"Label phải là 0 hoặc 1; nhận được {labels}."
        )

    if labels != {0, 1}:
        raise ValueError(
            "Dataset cần có cả hai lớp fake (1) và real (0)."
        )

    y = df[LABEL_COLUMN].astype(int)

    # 6. Chuyển feature về dạng số
    X = df[FEATURE_COLUMNS].apply(
        pd.to_numeric,
        errors="raise",
    )

    # 7. Kiểm tra feature, giữ nguyên NaN
    # XGBoost xử lý được NaN; không mặc định NaN là 0.
    for column in FEATURE_COLUMNS:
        for index, value in X[column].items():
            if pd.isna(value):
                continue

            try:
                validate_feature_value(column, value)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Feature '{column}' không hợp lệ "
                    f"ở dòng dữ liệu {index}: {exc}"
                ) from exc

    # 8. Kiểm tra domain trùng giữa hai lớp
    # Đọc lại domain để phát hiện một website có cả hai nhãn.
    domains = pd.concat(
        [
            fake_df["domain"].astype(str).str.lower().str.strip(),
            real_df["domain"].astype(str).str.lower().str.strip(),
        ],
        ignore_index=True,
    )

    if domains.duplicated().any():
        raise ValueError(
            "Có domain trùng giữa các mẫu. "
            "Hãy kiểm tra nhãn và loại bỏ trùng trước khi train."
        )

    # 9. Chia train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    print(f"Tổng số mẫu: {len(df)}")
    print(f"Số feature: {len(FEATURE_COLUMNS)}")
    print(f"Train: {len(X_train)}")
    print(f"Test: {len(X_test)}")
    print(f"Nhãn toàn bộ: {y.value_counts().to_dict()}")
    print(f"Giá trị thiếu:\n{X.isnull().sum()[X.isnull().sum() > 0]}")

    return X_train, X_test, y_train, y_test
