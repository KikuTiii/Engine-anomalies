import requests

url = "http://motor-inference-env.eba-w58rcav3.us-east-1.elasticbeanstalk.com"

# Verificar se a API esta no ar
response = requests.get(f"{url}/health")
print(response.json())  # {"status": "ok"}

# Realizar uma predicao
leitura = {
    "rotacao_rpm": 1800.0,
    "vibracao_mm_s": 8.5,
    "temperatura_c": 95.0,
    "corrente_a": 18.2,
}

response = requests.post(f"{url}/predict", json=leitura)
resultado = response.json()

print(f"Falha detectada : {resultado['falha']}")
for classe, prob in resultado["probabilidades"].items():
    print(f"  {classe:20s}: {prob:.2%}")