from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "data" / "motor.db"
MODEL_PATH = PROJECT_ROOT / "models" / "motor_classifier.joblib"