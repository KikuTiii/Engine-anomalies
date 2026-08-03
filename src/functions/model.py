from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_validate,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_PATH
from src.utils.preprocessing import FEATURE_COLS

CLASS_NAMES = {
    0: "Normal",
    1: "Desbalanceamento",
    2: "Superaquecimento",
    3: "Falha mecanica",
}

_PARAM_DIST = {
    "clf__n_estimators":    [100, 200, 300, 500],
    "clf__max_depth":       [None, 10, 20, 30],
    "clf__min_samples_split": [2, 5, 10],
    "clf__min_samples_leaf":  [1, 2, 4],
    "clf__max_features":    ["sqrt", "log2", 0.3, 0.5],
}


def _make_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
        )),
    ])


def cross_validate_model(X, y, cv: int = 5) -> dict:
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    scores = cross_validate(
        _make_pipeline(), X, y,
        cv=skf,
        scoring=["accuracy", "f1_macro"],
        n_jobs=-1,
    )
    return {
        "accuracy_mean": float(scores["test_accuracy"].mean()),
        "accuracy_std":  float(scores["test_accuracy"].std()),
        "f1_macro_mean": float(scores["test_f1_macro"].mean()),
        "f1_macro_std":  float(scores["test_f1_macro"].std()),
    }


def tune_hyperparameters(
    X_train, y_train, n_iter: int = 30, cv: int = 5
) -> tuple[Pipeline, dict, float]:
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    search = RandomizedSearchCV(
        _make_pipeline(),
        param_distributions=_PARAM_DIST,
        n_iter=n_iter,
        cv=skf,
        scoring="f1_macro",
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_, float(search.best_score_)


def train(X_train, y_train) -> Pipeline:
    pipeline = _make_pipeline()
    pipeline.fit(X_train, y_train)
    return pipeline


def evaluate(model, X_test, y_test, label_names: list = None) -> dict:
    y_pred = model.predict(X_test)
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "classification_report": classification_report(
            y_test, y_pred, target_names=label_names
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
    }


def save(pipeline: Pipeline, path: str = MODEL_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline}, path)


def load(path: str = MODEL_PATH) -> dict:
    return joblib.load(path)


def predict(
    vars: dict,
    artifact: dict = None,
    failure_threshold: float | None = None,
) -> dict:
    if artifact is None:
        artifact = load()

    pipeline = artifact["pipeline"]

    rotacao_rpm   = vars["rotacao_rpm"]
    vibracao_mm_s = vars["vibracao_mm_s"]
    temperatura_c = vars["temperatura_c"]
    corrente_a    = vars["corrente_a"]

    vibracao_por_rotacao = vibracao_mm_s / rotacao_rpm if rotacao_rpm != 0 else 0.0

    X = pd.DataFrame(
        [[
            rotacao_rpm,
            vibracao_mm_s,
            temperatura_c,
            corrente_a,
            rotacao_rpm,    # rotacao_mean (janela de 1 ponto)
            0.0,            # vibracao_std (janela de 1 ponto)
            temperatura_c,  # temperatura_max (janela de 1 ponto)
            corrente_a,     # corrente_mean (janela de 1 ponto)
            vibracao_por_rotacao,
        ]],
        columns=FEATURE_COLS,
    )

    probabilidades = pipeline.predict_proba(X)[0]

    if failure_threshold is not None:
        prob_normal = probabilidades[0]
        classe = int(probabilidades[1:].argmax()) + 1 if prob_normal < failure_threshold else 0
    else:
        classe = int(pipeline.predict(X)[0])

    return {
        "falha": CLASS_NAMES[classe],
        "probabilidades": {CLASS_NAMES[i]: round(float(p), 4) for i, p in enumerate(probabilidades)},
    }