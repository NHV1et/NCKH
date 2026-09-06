import yaml
from pathlib import Path
from xgboost import XGBClassifier

from src.preprocessing.dataset_loader import load_dataset

# D:\code\NCKH\AI_BOT\src\full_model
BASE_DIR = Path(__file__).resolve().parent

# D:\code\NCKH\AI_BOT
PROJECT_ROOT = BASE_DIR.parent.parent

CONFIG_PATH = BASE_DIR / "config.yaml"
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "dataset.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "full_model.json"

# LOAD CONFIG

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# LOAD DATASET

X_train, X_test, y_train, y_test = load_dataset(
    DATASET_PATH
)

# CREATE MODEL


model = XGBClassifier(
    n_estimators=config["model"]["n_estimators"],
    max_depth=config["model"]["max_depth"],
    learning_rate=config["model"]["learning_rate"],
    subsample=config["model"]["subsample"],
    colsample_bytree=config["model"]["colsample_bytree"],
    eval_metric="logloss"
)

# TRAIN
model.fit(X_train, y_train)

# SAVE MODEL
MODEL_DIR.mkdir(parents=True, exist_ok=True)

model.save_model(MODEL_PATH)

print("Train xong")
print(f"Model saved tại: {MODEL_PATH}")