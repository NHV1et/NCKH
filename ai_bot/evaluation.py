
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    RocCurveDisplay,
    PrecisionRecallDisplay,
)

from ai_bot.dataset_loader import load_dataset


# ==========================================
# PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "model" / "full_model.json"
CONFIG_PATH = BASE_DIR / "config.yaml"

RESULT_DIR = BASE_DIR / "evaluation_results"
THRESHOLD_PATH = RESULT_DIR / "thresholds.json"


# Mục tiêu chọn ngưỡng trên validation.
TARGET_RECALL = 0.95
TARGET_PRECISION = 0.95


# ==========================================
# MODEL
# ==========================================

def create_model(config):
    """Tạo model tạm với cấu hình giống train.py."""

    return XGBClassifier(
        n_estimators=config["model"]["n_estimators"],
        max_depth=config["model"]["max_depth"],
        learning_rate=config["model"]["learning_rate"],
        subsample=config["model"]["subsample"],
        colsample_bytree=config["model"]["colsample_bytree"],
        eval_metric="logloss",
        random_state=config["training"]["random_state"],
        objective="binary:logistic",
        n_jobs=-1,
    )


# ==========================================
# FIND THRESHOLDS
# ==========================================

def find_thresholds(
    y_val,
    prob_phishing,
    target_recall=TARGET_RECALL,
    target_precision=TARGET_PRECISION,
):
    """
    Chọn ngưỡng từ validation:
    - low: ưu tiên recall cao, hạn chế bỏ sót phishing.
    - high: ưu tiên precision cao cho kết luận phishing.

    Nếu không đạt mục tiêu precision, hàm chọn ngưỡng có
    precision tốt nhất trong các ngưỡng hợp lệ và báo rõ
    rằng mục tiêu chưa đạt.
    """

    candidates = [i / 100 for i in range(1, 100)]

    # Ngưỡng thấp: tìm ngưỡng cao nhất vẫn đạt recall mục tiêu.
    valid_low = []

    for threshold in candidates:
        pred = (prob_phishing >= threshold).astype(int)
        recall = recall_score(
            y_val, pred, pos_label=1, zero_division=0
        )

        if recall >= target_recall:
            valid_low.append(threshold)

    if valid_low:
        low = max(valid_low)
        recall_target_met = True
    else:
        # Không đạt recall mục tiêu: chọn recall cao nhất.
        recall_candidates = []

        for threshold in candidates:
            pred = (prob_phishing >= threshold).astype(int)
            recall = recall_score(
                y_val, pred, pos_label=1, zero_division=0
            )
            recall_candidates.append((threshold, recall))

        low, _ = max(
            recall_candidates,
            key=lambda item: (item[1], item[0]),
        )
        recall_target_met = False

    # Ngưỡng cao phải lớn hơn ngưỡng thấp.
    high_candidates = []

    for threshold in candidates:
        if threshold <= low:
            continue

        pred = (prob_phishing >= threshold).astype(int)

        # Bỏ qua ngưỡng không dự đoán mẫu phishing nào.
        if pred.sum() == 0:
            continue

        precision = precision_score(
            y_val, pred, pos_label=1, zero_division=0
        )

        high_candidates.append((threshold, precision))

    if not high_candidates:
        raise ValueError(
            "Không tìm được ngưỡng cao lớn hơn ngưỡng thấp "
            "có dự đoán phishing trên validation. "
            "Cần xem lại dữ liệu hoặc mục tiêu ngưỡng."
        )

    valid_high = [
        (threshold, precision)
        for threshold, precision in high_candidates
        if precision >= target_precision
    ]

    if valid_high:
        # Ngưỡng thấp nhất đạt precision mục tiêu.
        high, _ = min(valid_high, key=lambda item: item[0])
        precision_target_met = True
    else:
        # Vẫn trả về ngưỡng tốt nhất, nhưng không tuyên bố
        # rằng precision đã đạt mục tiêu đề ra.
        high, _ = max(
            high_candidates,
            key=lambda item: (item[1], -item[0]),
        )
        precision_target_met = False

    return {
        "low": float(low),
        "high": float(high),
        "target_recall": float(target_recall),
        "target_precision": float(target_precision),
        "recall_target_met": recall_target_met,
        "precision_target_met": precision_target_met,
    }


# ==========================================
# EVALUATION
# ==========================================

def evaluate_model():
    """Đánh giá model và lựa chọn ngưỡng ba mức."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model: {MODEL_PATH}\n"
            "Hãy chạy train.py trước."
        )

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy config: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Model chính đã được train bởi train.py.
    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))

    # Dữ liệu test vẫn được giữ nguyên theo load_dataset().
    X_train, X_test, y_train, y_test = load_dataset()

    if len(X_test) == 0:
        raise ValueError("Tập test không có dữ liệu.")

    if len(set(y_test)) < 2:
        print(
            "Cảnh báo: tập test chỉ có một lớp; "
            "ROC-AUC sẽ không được tính."
        )

    # Chia phần train thành fit và validation.
    # Validation KHÔNG được dùng để fit model tạm.
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train,
        y_train,
        test_size=0.2,
        random_state=config["training"]["random_state"],
        stratify=y_train,
    )

    # Huấn luyện model tạm để chọn ngưỡng.
    threshold_model = create_model(config)
    threshold_model.fit(X_fit, y_fit)

    classes_val = list(threshold_model.classes_)
    if 1 not in classes_val:
        raise ValueError(
            f"Model validation không có lớp 1: {classes_val}"
        )

    phishing_index_val = classes_val.index(1)
    val_probabilities = threshold_model.predict_proba(X_val)
    val_prob_phishing = val_probabilities[:, phishing_index_val]

    thresholds = find_thresholds(
        y_val,
        val_prob_phishing,
    )

    low = thresholds["low"]
    high = thresholds["high"]

    # Lưu ngưỡng để infer.py có thể đọc sau này.
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    with open(THRESHOLD_PATH, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, ensure_ascii=False, indent=4)

    # ======================================
    # PREDICTION ON TEST
    # ======================================

    classes = list(model.classes_)
    if 1 not in classes:
        raise ValueError(
            f"Model chính không có lớp 1: {classes}"
        )

    phishing_index = classes.index(1)

    y_probability = model.predict_proba(X_test)
    y_prob_phishing = y_probability[:, phishing_index]

    # Kết quả nhị phân ở ngưỡng mặc định 0.5,
    # dùng để giữ các metric truyền thống.
    y_pred = model.predict(X_test)

    # Ba mức quyết định dựa trên hai ngưỡng.
    def classify_probability(probability):
        if probability < low:
            return "real"
        if probability < high:
            return "suspicious"
        return "phishing"

    y_pred_3class = [
        classify_probability(prob)
        for prob in y_prob_phishing
    ]

    # ======================================
    # BINARY METRICS
    # ======================================

    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(
        y_test, y_pred, pos_label=1, zero_division=0
    )

    recall = recall_score(
        y_test, y_pred, pos_label=1, zero_division=0
    )

    f1 = f1_score(
        y_test, y_pred, pos_label=1, zero_division=0
    )

    roc_auc = (
        roc_auc_score(y_test, y_prob_phishing)
        if len(set(y_test)) == 2
        else None
    )

    loss = log_loss(
        y_test,
        y_probability,
        labels=model.classes_,
    )

    # ======================================
    # THREE-LEVEL SUMMARY
    # ======================================

    result_counts = pd.Series(y_pred_3class).value_counts()

    real_count = int(result_counts.get("real", 0))
    suspicious_count = int(result_counts.get("suspicious", 0))
    phishing_count = int(result_counts.get("phishing", 0))

    # Những website được đánh dấu cần chú ý gồm suspicious
    # và phishing. Tính recall/precision trên nhãn thật nhị phân.
    y_flagged = [
        0 if result == "real" else 1
        for result in y_pred_3class
    ]

    flagged_precision = precision_score(
        y_test, y_flagged, pos_label=1, zero_division=0
    )

    flagged_recall = recall_score(
        y_test, y_flagged, pos_label=1, zero_division=0
    )

    # Precision riêng cho nhóm được kết luận phishing.
    phishing_mask = [
        result == "phishing" for result in y_pred_3class
    ]

    if any(phishing_mask):
        high_confidence_precision = sum(
            int(actual) == 1
            for actual, selected in zip(y_test, phishing_mask)
            if selected
        ) / sum(phishing_mask)
    else:
        high_confidence_precision = None

    # ======================================
    # PRINT RESULTS
    # ======================================

    print("=" * 60)
    print("         XGBOOST PHISHING DETECTION")
    print("                 EVALUATION")
    print("=" * 60)

    print(f"\nFit samples       : {len(X_fit)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples      : {len(X_test)}")

    print("\n--- Binary metrics (threshold = 0.5) ---")
    print(f"Accuracy    : {accuracy:.4f}")
    print(f"Precision   : {precision:.4f}")
    print(f"Recall      : {recall:.4f}")
    print(f"F1-score    : {f1:.4f}")
    print(
        f"ROC-AUC     : {roc_auc:.4f}"
        if roc_auc is not None
        else "ROC-AUC     : Không tính được."
    )
    print(f"Log Loss    : {loss:.4f}")

    print("\n--- Selected thresholds (validation) ---")
    print(f"T_low       : {low:.2f}")
    print(f"T_high      : {high:.2f}")
    print(
        f"Recall target {TARGET_RECALL:.0%}: "
        f"{'Đạt' if thresholds['recall_target_met'] else 'Chưa đạt'}"
    )
    print(
        f"Precision target {TARGET_PRECISION:.0%}: "
        f"{'Đạt' if thresholds['precision_target_met'] else 'Chưa đạt'}"
    )

    print("\n--- Three-level predictions on test ---")
    print(f"Real       : {real_count}")
    print(f"Suspicious : {suspicious_count}")
    print(f"Phishing   : {phishing_count}")

    print("\n--- Security-oriented test metrics ---")
    print(f"Flagged precision: {flagged_precision:.4f}")
    print(f"Flagged recall   : {flagged_recall:.4f}")

    if high_confidence_precision is not None:
        print(
            "Phishing precision among high-risk predictions: "
            f"{high_confidence_precision:.4f}"
        )
    else:
        print("Không có mẫu nào được kết luận phishing.")

    # ======================================
    # CONFUSION MATRIX
    # ======================================

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=[0, 1],
    )

    print("\n--- Confusion matrix (threshold = 0.5) ---")
    print(cm)

    print("\n--- Classification report (threshold = 0.5) ---")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["Real", "Fake/Phishing"],
            zero_division=0,
        )
    )

    # ======================================
    # SAVE PLOTS
    # ======================================

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Real", "Fake/Phishing"],
    )
    disp.plot()
    plt.title("Confusion Matrix - XGBoost")
    plt.tight_layout()
    plt.savefig(
        RESULT_DIR / "confusion_matrix.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    if roc_auc is not None:
        RocCurveDisplay.from_predictions(
            y_test, y_prob_phishing
        )
        plt.title(f"ROC Curve - AUC = {roc_auc:.4f}")
        plt.tight_layout()
        plt.savefig(
            RESULT_DIR / "roc_curve.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        PrecisionRecallDisplay.from_predictions(
            y_test, y_prob_phishing
        )
        plt.title("Precision-Recall Curve - XGBoost")
        plt.tight_layout()
        plt.savefig(
            RESULT_DIR / "precision_recall_curve.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    # Lưu các metric nhị phân và metric ba mức.
    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "log_loss": loss,
        "threshold_low": low,
        "threshold_high": high,
        "real_predictions": real_count,
        "suspicious_predictions": suspicious_count,
        "phishing_predictions": phishing_count,
        "flagged_precision": flagged_precision,
        "flagged_recall": flagged_recall,
        "high_confidence_phishing_precision": high_confidence_precision,
        "recall_target_met": thresholds["recall_target_met"],
        "precision_target_met": thresholds["precision_target_met"],
    }

    pd.DataFrame([metrics]).to_csv(
        RESULT_DIR / "metrics.csv",
        index=False,
    )

    # Lưu từng dự đoán để kiểm tra lại sau.
    predictions = pd.DataFrame({
        "y_true": list(y_test),
        "prob_phishing": y_prob_phishing,
        "predicted_label": y_pred_3class,
    })
    predictions.to_csv(
        RESULT_DIR / "test_predictions.csv",
        index=False,
    )

    print("\nĐã lưu kết quả tại:")
    print(RESULT_DIR)
    print(f"Ngưỡng: {THRESHOLD_PATH}")


if __name__ == "__main__":
    evaluate_model()
