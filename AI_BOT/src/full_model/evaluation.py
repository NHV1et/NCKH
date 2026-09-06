from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from xgboost import XGBClassifier

from src.preprocessing.dataset_loader import load_dataset

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



# PATH

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "src"
    / "full_model"
    / "model"
    / "full_model.json"
)

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "dataset.csv"
)


# LOAD MODEL

model = XGBClassifier()
model.load_model(MODEL_PATH)


# LOAD DATA

X_train, X_test, y_train, y_test = load_dataset(
    DATASET_PATH
)



# PREDICTION


y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)

# Xác suất phishing - class 1
y_prob_phishing = y_probability[:, 1]



# METRICS

accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    pos_label=1,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    pos_label=1,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    pos_label=1,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    y_prob_phishing
)

loss = log_loss(
    y_test,
    y_probability
)

# PRINT RESULTS


print("=" * 60)
print("        XGBOOST PHISHING DETECTION")
print("              EVALUATION")
print("=" * 60)

print(f"\nAccuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1-score : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"Log Loss : {loss:.4f}")



# CONFUSION MATRIX


cm = confusion_matrix(
    y_test,
    y_pred
)

print("=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(cm)


# CLASSIFICATION REPORT

print("=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "Real",
            "Phishing"
        ],
        zero_division=0
    )
)


# ==========================================
# 1. CONFUSION MATRIX PLOT
# ==========================================

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Real", "Phishing"]
)

disp.plot()

plt.title("Confusion Matrix - XGBoost")
plt.tight_layout()
plt.show()


# ==========================================
# 2. ROC CURVE
# ==========================================

RocCurveDisplay.from_predictions(
    y_test,
    y_prob_phishing
)

plt.title(
    f"ROC Curve - AUC = {roc_auc:.4f}"
)

plt.tight_layout()
plt.show()


