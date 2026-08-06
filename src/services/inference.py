from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.functions.model import load, predict


artifact: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    artifact.update(load())
    yield
    artifact.clear()


app = FastAPI(title="Motor Fault Classifier", lifespan=lifespan)


class SensorReading(BaseModel):
    rotacao_rpm: float = Field(gt=0, description="Rotacao em RPM")
    vibracao_mm_s: float = Field(gt=0, description="Vibracao em mm/s")
    temperatura_c: float = Field(gt=0, description="Temperatura em graus Celsius")
    corrente_a: float = Field(gt=0, description="Corrente eletrica em Amperes")


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "motor-inference",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict_endpoint(reading: SensorReading):
    return predict(
        vars=reading.model_dump(),
        artifact=artifact,
    )