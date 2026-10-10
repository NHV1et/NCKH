from pathlib import Path
import sys
import logging
import yaml
from xgboost import XGBClassifier
from ai_bot.dataset_loader import load_dataset
import os

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
# Ghi log ra stderr để không làm hỏng MCP stdio
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Thư mục NCKH/ai_bot/
PROJECT_DIR = Path(__file__).resolve().parent

# Paths
CONFIG_PATH = PROJECT_DIR / "config.yaml"
FAKE_DATASET_PATH = PROJECT_DIR / "data" / "fake.csv"
REAL_DATASET_PATH = PROJECT_DIR / "data" / "real.csv"

MODEL_DIR = PROJECT_DIR / "model"
MODEL_PATH = MODEL_DIR / "full_model.json"


def train_model() -> dict:
    """Huấn luyện và lưu model phát hiện website phishing."""

    # Kiểm tra file đầu vào
    required_files = [
        CONFIG_PATH,
        FAKE_DATASET_PATH,
        REAL_DATASET_PATH,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file: {path}"
            )

    logger.info("Đang đọc cấu hình...")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Load dataset
    logger.info("Đang tải dataset...")

    X_train, X_test, y_train, y_test = load_dataset(
        fake_path=FAKE_DATASET_PATH,
        real_path=REAL_DATASET_PATH,
        test_size=config["training"]["test_size"],
        random_state=config["training"]["random_state"],
    )

    # Tạo model
    model = XGBClassifier(
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

    # Train
    logger.info("Đang huấn luyện model...")
    model.fit(X_train, y_train)

    # Lưu model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_PATH))

    logger.info("Huấn luyện model hoàn tất.")

    return {
        "status": "success",
        "message": "Train model thành công!",
        "model_path": str(MODEL_PATH),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
    }


if __name__ == "__main__":
    try:
        result = train_model()
        print(result)
    except Exception:
        logger.exception("Train model thất bại.")
        raise
