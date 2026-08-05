# Deploy Manual na AWS — macOS e Linux

Guia para publicar a API de inferencia no Elastic Beanstalk usando o Amazon ECR como registro de imagens Docker.

## Variaveis

Substitua os placeholders abaixo pelos valores da sua conta antes de executar os comandos:

| Placeholder | Descricao | Exemplo |
|---|---|---|
| `<AWS_ACCOUNT_ID>` | ID numerico da sua conta AWS | `975037863921` |
| `us-east-1` | Regiao AWS escolhida | `us-east-1` |

---

## Pre-requisitos

### 1. Instalar AWS CLI e EB CLI

```bash
brew install awscli awsebcli
```

### 2. Configurar credenciais

```bash
aws configure
```

Preencha com os dados da sua conta:

```
AWS Access Key ID:     <sua access key>
AWS Secret Access Key: <sua secret key>
Default region name:   us-east-1
Default output format: json
```

> As chaves sao geradas em: **AWS Console → seu usuario → Security credentials → Access keys → Create access key**

---

## Configurar o Dockerrun.aws.json

Edite o arquivo `Dockerrun.aws.json` substituindo `<AWS_ACCOUNT_ID>` e `us-east-1` pelos valores da sua conta:

```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/motor-inference:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8000,
      "HostPort": 80
    }
  ]
}
```

---

## Criar o repositorio no ECR

Via console: **Amazon ECR → Registros privados → Repositorios → Criar repositorio**

Nome: `motor-inference`

Ou via CLI:

```bash
aws ecr create-repository --repository-name motor-inference --region us-east-1
```

---

## Build e Push da Imagem

### 1. Autenticar o Docker no ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  729608198101.dkr.ecr.us-east-1.amazonaws.com
```

### 2. Build da imagem

```bash
docker build -t motor-inference .
```

### 3. Tag da imagem

```bash
docker tag motor-inference:latest \
  729608198101.dkr.ecr.us-east-1.amazonaws.com/motor-inference:latest
```

### 4. Push para o ECR

```bash
docker push \
  729608198101.dkr.ecr.us-east-1.amazonaws.com/motor-inference:latest
```

---

## Deploy no Elastic Beanstalk

### Primeiro deploy

```bash
eb init motor-inference --platform docker --region us-east-1
eb create motor-inference-env --single
```

O flag `--single` cria um ambiente sem load balancer (~$7.50/mes vs ~$25/mes com load balancer).

### Verificar o ambiente

```bash
eb status
```

A URL da aplicacao aparece no campo `CNAME`. Acesse `/docs` para a documentacao interativa da API.

---

## Atualizar o Deploy

A cada nova versao do modelo ou da API, repita os passos de build e push e execute:

```bash
eb deploy
```

---

## Solucao de Problemas na Atualizacao

E nesta etapa que os problemas costumam aparecer: o build e o push funcionam, mas a atualizacao nao chega ao ambiente ou o deploy falha. A tabela abaixo mapeia cada sintoma a sua correcao:

| Sintoma | Causa | Correcao |
|---|---|---|
| Deploy conclui com sucesso, mas a API continua com o codigo antigo | Sem o `.ebignore`, o EB CLI empacota o ultimo commit do git em vez do `Dockerrun.aws.json` | Passo 1 |
| `The ECR service failed to authenticate your private repository` | Role da instancia sem permissao de leitura no ECR | Passo 2 |
| Container nao inicia apos o deploy ("exec format error" no `eb logs`) | Imagem buildada em Mac Apple Silicon (`arm64`) nao roda na EC2 (`x86_64`) | Passo 3 |

### Passo 1: Criar o .ebignore

Crie um arquivo chamado `.ebignore` na raiz do projeto com o conteudo abaixo:

```
*
!Dockerrun.aws.json
```

Ele garante que o `eb deploy` envie **apenas** o `Dockerrun.aws.json` para o Elastic Beanstalk, que entao puxa a imagem pronta do ECR.

> **Sem esse arquivo, o ECR e ignorado silenciosamente:** em projetos com git, o EB CLI empacota o **ultimo commit** (incluindo o `Dockerfile` e o codigo fonte). O Elastic Beanstalk da preferencia ao `Dockerfile` e builda a imagem na propria instancia, entao alteracoes nao commitadas nunca chegam ao ambiente, mesmo com a imagem nova no ECR.

Um jeito facil de conferir: com o `.ebignore` correto, o upload do `eb deploy` e um zip minusculo (menos de 1 KB). Se estiver subindo varios MB, o git archive esta sendo usado.

### Passo 2: Autorizar a instancia a acessar o ECR

Depois do `.ebignore`, o deploy passa a depender do pull da imagem no ECR, e pode falhar com:

```
ERROR   Instance deployment: The ECR service failed to authenticate your private repository. The deployment failed.
```

A instancia EC2 do Elastic Beanstalk usa o role `aws-elasticbeanstalk-ec2-role` como identidade (e o "usuario" da maquina na AWS). Por padrao esse role vem apenas com as policies basicas do Beanstalk, sem permissao de leitura no ECR. Anexe a policy gerenciada `AmazonEC2ContainerRegistryReadOnly` ao role.

Via console: **IAM → Roles → aws-elasticbeanstalk-ec2-role → Add permissions → Attach policies → buscar `AmazonEC2ContainerRegistryReadOnly` → Attach**

Ou via CLI:

```bash
aws iam attach-role-policy \
  --role-name aws-elasticbeanstalk-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

Essa policy da acesso de **somente leitura**: autenticar no ECR e baixar imagens (o equivalente a `docker login` + `docker pull`), sem permissao de subir ou apagar nada. A mudanca vale na hora, sem reiniciar a instancia: basta rodar `eb deploy` de novo.

### Passo 3: Build para a arquitetura da EC2 (Apple Silicon)

Em Macs com Apple Silicon (M1/M2/M3/M4), o `docker build` gera por padrao uma imagem `arm64`, que nao roda na instancia EC2 do Elastic Beanstalk (arquitetura `x86_64`): o container falha ao iniciar com "exec format error". Refaca o build forcando a plataforma:

```bash
docker build --platform linux/amd64 -t motor-inference .
```

Depois repita o tag, o push e o `eb deploy`.

---

## Encerrar o Ambiente

Para evitar cobranças quando o ambiente nao estiver em uso:

```bash
eb terminate motor-inference-env
```

---

## Chamar o Endpoint via Python

Substitua `<URL>` pelo valor do campo `CNAME` retornado pelo `eb status`.

```python
import requests

url = "http://<URL>"

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
```

Resposta esperada:

```
Falha detectada : Superaquecimento
  Normal              : 0.00%
  Desbalanceamento    : 28.50%
  Superaquecimento    : 70.50%
  Falha mecanica      : 1.00%
```

### Documentacao interativa

Acesse no navegador:

```
http://<URL>/docs
```

---

## Custos estimados (single-instance)

| Recurso | Custo estimado/mes |
|---|---|
| EC2 t3.micro | ~$7.50 |
| ECR (armazenamento) | ~$0.02 |
| **Total** | **~$7.52** |

> Lembre de encerrar o ambiente apos o uso para evitar cobranças desnecessarias.