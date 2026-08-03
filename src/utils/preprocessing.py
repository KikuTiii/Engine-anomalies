import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

FEATURE_COLS = [
    "rotacao_rpm",
    "vibracao_mm_s",
    "temperatura_c",
    "corrente_a",
    "rotacao_mean",
    "vibracao_std",
    "temperatura_max",
    "corrente_mean",
    "vibracao_por_rotacao",
]

TARGET_COL = "falha"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values(["motor_id", "timestamp"])

    groups = df.groupby("motor_id")

    df["rotacao_mean"] = groups["rotacao_rpm"].transform(
        lambda s: s.rolling(5, min_periods=1).mean()
    )
    df["vibracao_std"] = groups["vibracao_mm_s"].transform(
        lambda s: s.rolling(5, min_periods=1).std().fillna(0)
    )
    df["temperatura_max"] = groups["temperatura_c"].transform(
        lambda s: s.rolling(5, min_periods=1).max()
    )
    df["corrente_mean"] = groups["corrente_a"].transform(
        lambda s: s.rolling(5, min_periods=1).mean()
    )

    df["vibracao_por_rotacao"] = df["vibracao_mm_s"] / df["rotacao_rpm"].replace(0, np.nan)
    df = df.dropna(subset=FEATURE_COLS)
    return df


def prepare_dataset(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple:
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    return X_train, X_test, y_train, y_test