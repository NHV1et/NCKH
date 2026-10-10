from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from xgboost import XGBClassifier

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

RESULT_DIR = BASE_DIR / "evaluation_results"


# ==========================================
# EVALUATION
# ==========================================

def evaluate_model():
    """
    Đánh giá model XGBoost trên tập test.

    Dataset được load và chia train/test bởi dataset_loader.py.
    Các nhãn giả định:
        0 = real
        1 = fake/phishing
    """

    # Kiểm tra model
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model: {MODEL_PATH}\n"
            "Hãy chạy train.py trước."
        )

    # Load model
    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))

    # Load dữ liệu
    X_train, X_test, y_train, y_test = load_dataset()

    if len(X_test) == 0:
        raise ValueError("Tập test không có dữ liệu.")

    # Dự đoán
    y_pred = model.predict(X_test)
    y_probability = model.predict_proba(X_test)

    # Xác định đúng cột xác suất lớp fake
    classes = list(model.classes_)

    if 1 not in classes:
        raise ValueError(
            f"Model không có lớp 1. Các lớp hiện có: {classes}"
        )

    fake_index = classes.index(1)
    y_prob_fake = y_probability[:, fake_index]

    # ======================================
    # METRICS
    # ======================================

    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(
        y_test,
        y_pred,
        pos_label=1,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        y_pred,
        pos_label=1,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        y_pred,
        pos_label=1,
        zero_division=0,
    )

    # ROC-AUC cần tập test có cả hai lớp
    if len(set(y_test)) == 2:
        roc_auc = roc_auc_score(y_test, y_prob_fake)
    else:
        roc_auc = None

    loss = log_loss(
        y_test,
        y_probability,
        labels=model.classes_,
    )

    # ======================================
    # PRINT RESULTS
    # ======================================

    print("=" * 60)
    print("         XGBOOST PHISHING DETECTION")
    print("                 EVALUATION")
    print("=" * 60)

    print(f"\nTest samples: {len(y_test)}")
    print(f"Accuracy    : {accuracy:.4f}")
    print(f"Precision   : {precision:.4f}")
    print(f"Recall      : {recall:.4f}")
    print(f"F1-score    : {f1:.4f}")

    if roc_auc is not None:
        print(f"ROC-AUC     : {roc_auc:.4f}")
    else:
        print("ROC-AUC     : Không tính được vì tập test chỉ có một lớp.")

    print(f"Log Loss    : {loss:.4f}")

    # ======================================
    # CONFUSION MATRIX
    # ======================================

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=[0, 1],
    )

    print("\n" + "=" * 60)
    print("CONFUSION MATRIX")
    print("=" * 60)

    print(cm)

    # ======================================
    # CLASSIFICATION REPORT
    # ======================================

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)

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

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Confusion Matrix
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
    plt.show()
    plt.close()

    # 2. ROC Curve
    if roc_auc is not None:
        RocCurveDisplay.from_predictions(
            y_test,
            y_prob_fake,
        )

        plt.title(f"ROC Curve - AUC = {roc_auc:.4f}")
        plt.tight_layout()

        plt.savefig(
            RESULT_DIR / "roc_curve.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()
        plt.close()

        # 3. Precision-Recall Curve
        PrecisionRecallDisplay.from_predictions(
            y_test,
            y_prob_fake,
        )

        plt.title("Precision-Recall Curve - XGBoost")
        plt.tight_layout()

        plt.savefig(
            RESULT_DIR / "precision_recall_curve.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()
        plt.close()

    # ======================================
    # SAVE METRICS TO CSV
    # ======================================

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "log_loss": loss,
    }

    pd.DataFrame([metrics]).to_csv(
        RESULT_DIR / "metrics.csv",
        index=False,
    )

    print("\nĐã lưu kết quả tại:")
    print(RESULT_DIR)


if __name__ == "__main__":
    evaluate_model()