"""

Exemplos de chamada da API apos rodar o container localmente:

1. Buildar a imagem do container:
docker build -t engine_anomalies .

2. Rodar o container localmente:
docker run -p 8000:8000 engine_anomalies

3. Executar este script para testar a API:
python test.py

tambem é possivel testar via curl:
    curl -X 'POST' \
    'http://localhost:8000/predict' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "data": {
        "rotacao_rpm": 1780,
        "vibracao_mm_s": 2.5,
        "temperatura_c": 75.0,
        "corrente_a": 12.3
    }
    }'
"""

import requests

BASE_URL = "http://localhost:8000"

def predict(rotacao_rpm: float, vibracao_mm_s: float, temperatura_c: float, corrente_a: float) -> dict:
    payload = {
            "rotacao_rpm": rotacao_rpm,
            "vibracao_mm_s": vibracao_mm_s,
            "temperatura_c": temperatura_c,
            "corrente_a": corrente_a
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":

    exemplos = [
        {
            "rotacao_rpm": 1780,
            "vibracao_mm_s": 2.5,
            "temperatura_c": 75.0,
            "corrente_a": 12.3
        },
        {
            "rotacao_rpm": 1750,
            "vibracao_mm_s": 9.8,
            "temperatura_c": 78.0,
            "corrente_a": 13.5
        },
        {
            "rotacao_rpm": 1760,
            "vibracao_mm_s": 3.2,
            "temperatura_c": 110.0,
            "corrente_a": 15.0
        }
    ]

    # Teste de predição
    for exemplo in exemplos:
        prediction_response = predict(**exemplo)
        print(f"Prediction Response for {exemplo}:", prediction_response)