# projeto-motor-anomalias






# Sobre ambiente vitural

1. Criando o ambiente

```python
python3.11 -m venv .venv
```

2. Ativar o ambiente

2.1. macOS:

```python
source .venv/bin/activate
```

2.2. win:

```python
.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```python
pip install -r requirements.txt
```

# API de inferencia

A API foi criada com FastAPI em `src/services/inference.py` e expoe o endpoint `POST /predict`, que consome o modelo treinado.

## Pre-requisitos

1. Ambiente virtual ativado e dependencias instaladas (passos acima).

2. Instalar o `uvicorn` (servidor ASGI, nao esta no requirements.txt):

```bash
pip install uvicorn
```

3. Modelo treinado disponivel em `models/random_forest_model.joblib` (caminho definido em `src/config.py`).

## Executando a API

A partir da raiz do projeto (necessario, pois o caminho do modelo e relativo):

```bash
uvicorn src.services.inference:app --reload
```

A API sobe em `http://127.0.0.1:8000`. A documentacao interativa (Swagger) fica em `http://127.0.0.1:8000/docs`.

## Exemplo de requisicao

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rotacao_rpm": 1800.0,
    "vibracao_mm_s": 6.5,
    "temperatura_c": 60.0,
    "corrente_a": 16.2
  }'
```

Resposta esperada:

```json
{
  "falha": "Desbalanceamento",
  "probabilidades": {
    "Normal": 0.12,
    "Desbalanceamento": 0.75,
    "Superaquecimento": 0.08,
    "Falha mecanica": 0.05
  }
}
```

# Executando com Docker

A API pode ser executada em um container Docker, sem necessidade de ambiente virtual local. O `Dockerfile` na raiz do projeto usa a imagem `python:3.11-slim`, instala as dependencias do `requirements.txt` e copia o codigo (`src/`) e o modelo treinado (`models/`).

## Pre-requisitos

1. Docker instalado e em execucao (Docker Desktop no macOS/Windows).
2. Modelo treinado disponivel em `models/random_forest_model.joblib`, pois ele e copiado para dentro da imagem no build.

## 1. Build da imagem

A partir da raiz do projeto:

```bash
docker build -t motor-anomalias-api .
```

Isso cria a imagem local com o nome `motor-anomalias-api`. Para verificar:

```bash
docker images | grep motor-anomalias-api
```

## 2. Subir o container

```bash
docker run -d --name motor-anomalias -p 8000:8000 motor-anomalias-api
```

Explicando as flags:

- `-d`: roda o container em segundo plano (detached).
- `--name motor-anomalias`: nome do container, para facilitar parar/remover depois.
- `-p 8000:8000`: mapeia a porta 8000 do container para a porta 8000 da maquina local.

A API fica disponivel em `http://localhost:8000` e o Swagger em `http://localhost:8000/docs`.

## 3. Consumir a API

Verificar se a API esta no ar:

```bash
curl http://localhost:8000/health
```

Fazer uma predicao:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rotacao_rpm": 1800.0,
    "vibracao_mm_s": 6.5,
    "temperatura_c": 60.0,
    "corrente_a": 16.2
  }'
```

## 4. Gerenciar o container

Ver os logs da aplicacao:

```bash
docker logs -f motor-anomalias
```

Parar o container:

```bash
docker stop motor-anomalias
```

Iniciar novamente (sem novo build):

```bash
docker start motor-anomalias
```

Remover o container (necessario antes de subir outro com o mesmo nome):

```bash
docker rm -f motor-anomalias
```

## Observacoes

- Apos alterar o codigo ou retreinar o modelo, e preciso refazer o build (`docker build`) e recriar o container para que as mudancas tenham efeito.
- O `.dockerignore` exclui `.venv/`, `notebooks/`, `data/` e arquivos de cache do build, mantendo a imagem menor.
- Se a porta 8000 ja estiver em uso na maquina, basta trocar o mapeamento, por exemplo `-p 8080:8000` (a API passa a responder em `http://localhost:8080`).