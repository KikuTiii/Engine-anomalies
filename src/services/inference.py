from fastapi import FastAPI
from src.functions.model import predict
from pydantic import BaseModel

app = FastAPI(
    title="Engine Anomalies API",
)

class inputData(BaseModel):
    rotacao_rpm: float
    vibracao_mm_s: float
    temperatura_c: float
    corrente_a: float

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

@app.post("/predict")
def make_prediction(vars: inputData) -> dict:
    """
    Make a prediction using the trained model.

    Args:
        vars (dict): A dictionary containing the input variables for prediction.

    Returns:
        dict: A dictionary containing the prediction results.
    """
    predicao = predict(vars=vars.model_dump())
    return predicao