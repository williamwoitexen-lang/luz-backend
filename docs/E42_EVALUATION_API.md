# 4x2 Evaluation API (Sistema e42)

API para integração com avaliação de funcionários 4x2 via Power Automate. Sistema que captura forças (Strengths) e fraquezas (Weaknesses) de colaboradores para criação de planos de ação com IA.

## Overview

- **Prefix**: `/api/v1/e42`
- **Tag**: `4x2-evaluation`
- **Integração**: Power Automate → CRM Dynamics → LUZ Backend

## Endpoints

### 1. GET /evaluation - Avaliação Completa

Busca avaliação 4x2 completa (forças + fraquezas).

**Request:**
```bash
POST /api/v1/e42/evaluation
Content-Type: application/json

{
    "user_email": "employee-teste@electrolux.com",
    "identificator": "104"
}
```

**Response (200 OK):**
```json
{
    "user_email": "employee-teste@electrolux.com",
    "user_id": "user123",
    "weaknesses": [
        {
            "comment": "teste8",
            "selection": "GR: Learning ability",
            "evaluation_id": "ad3cad96-06ca-f011-8544-002248379316"
        },
        {
            "comment": "test7",
            "selection": "GR: Coaching others & self",
            "evaluation_id": "bec61e95-06ca-f011-8544-002248e0b02d"
        }
    ],
    "strengths": [
        {
            "comment": "teste2",
            "selection": "EN: Leading others and Self",
            "evaluation_id": "e7b85c8a-06ca-f011-8544-002248379316"
        },
        {
            "comment": "teste5",
            "selection": "OP: Cross-collaboration & Networking",
            "evaluation_id": "e5c7b88e-06ca-f011-8544-002248e0b02d"
        },
        {
            "comment": "teste3",
            "selection": "OP: Consumer & Customer Focus",
            "evaluation_id": "f0c7b88e-06ca-f011-8544-002248e0b02d"
        },
        {
            "comment": "teste1",
            "selection": "EN: Deliver Results",
            "evaluation_id": "fac7b88e-06ca-f011-8544-002248e0b02d"
        }
    ],
    "total_evaluations": 6,
    "evaluation_timestamp": "2026-02-26T10:30:00Z",
    "success": true
}
```

---

### 2. GET /evaluation/weaknesses-only - Apenas Fraquezas

Versão simplificada que retorna APENAS as fraquezas em formato de lista simples.

**Request:**
```bash
POST /api/v1/e42/evaluation/weaknesses-only
Content-Type: application/json

{
    "user_email": "employee-teste@electrolux.com",
    "identificator": "104"
}
```

**Response (200 OK):**
```json
{
    "user_email": "employee-teste@electrolux.com",
    "user_id": "user123",
    "weaknesses": [
        "teste8",
        "test7"
    ]
}
```

---

## Fluxo de Processamento

```
1. Requisição chega ao endpoint
   ↓
2. Chama Power Automate com email + ID da avaliação
   ↓
3. Power Automate acessa CRM Dynamics e retorna lista de avaliações
   ↓
4. Backend processa resposta:
   - Filtra apenas tipo "Individual" (ignora Manager)
   - Separa em "Weakness" e "Strength"
   - Extrai comentários, categorias e IDs
   ↓
5. Busca ID interno do usuário no banco (tabela users, coluna email)
   ↓
6. Retorna dados formatados (sem persistir no banco)
```

---

## Integração com LLM Server

Quando o usuário faz uma pergunta, o chat pode utilizar as fraquezas retornadas pela API:

```python
# Exemplo: Usar dados de avaliação para contextualizar

response = requests.post(
    "http://localhost:8000/api/v1/e42/evaluation",
    json={
        "user_email": "employee@electrolux.com",
        "identificator": "104"
    }
)

weaknesses = response.json()["weaknesses"]
weakness_comments = [w["comment"] for w in weaknesses]

prompt = f"""
Crie um plano de ação para {user_email} baseado em:
Fraquezas identificadas: {weakness_comments}

Considere ações práticas e mensuráveis.
"""

response = llm_server.chat(prompt)
```

---

## Tratamento de Erros

| Status | Descrição |
|--------|-----------|
| 200    | Avaliação obtida com sucesso |
| 404    | Usuário não encontrado em `users` (retorna user_id=null) |
| 500    | Erro ao chamar Power Automate |

**Exemplo de erro:**
```json
{
    "detail": "Erro ao buscar dados do Power Automate: Connection timeout"
}
```

---

## Observações Importantes

### Filtragem de Dados
- ✅ Apenas avaliações tipo **"Individual"** são processadas
- ❌ Avaliações tipo "Manager" são ignoradas
- ✅ Apenas comentários não-vazios são incluídos
- ✅ Email é validado (deve corresponder ao request)

### Persistência
- ❌ A API **NÃO** persiste dados no banco de dados
- ✅ Os dados são retornados na resposta e podem ser consumidos em tempo real
- ℹ️ A coluna `e42_evaluations` da tabela `user_preferences` foi descontinuada

### Categorias de Fraquezas/Forças
Baseadas em nomes como:
- `EN: Leading others and Self`
- `GR: Learning ability`
- `OP: Cross-collaboration & Networking`
- `OP: Consumer & Customer Focus`
- `EN: Deliver Results`
- `GR: Coaching others & self`

---

## Exemplo Completo: cURL

```bash
curl -X POST "http://localhost:8000/api/v1/e42/evaluation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "employee-teste@electrolux.com",
    "identificator": "104"
  }'
```

---

## Exemplo: Python/Requests

```python
import requests

url = "http://localhost:8000/api/v1/e42/evaluation"
payload = {
    "user_email": "employee-teste@electrolux.com",
    "identificator": "104"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    data = response.json()
    print(f"Usuário: {data['user_email']}")
    print(f"Fraquezas: {[w['comment'] for w in data['weaknesses']]}")
    print(f"Forças: {[s['comment'] for s in data['strengths']]}")
```

---

## Configuração de Variáveis de Ambiente

As seguintes variáveis de ambiente **obrigatórias** devem ser configuradas no Azure ou arquivo `.env`:

### Variáveis Necessárias

```bash
# Power Automate URL (obrigatória)
# Endpoint do Power Automate que realiza a chamada ao CRM Dynamics
POWER_AUTOMATE_URL=https://your-environment.e8.environment.api.powerplatform.com/...

# Assinatura da requisição (obrigatória)  
# Parâmetro 'sig' para validar a chamada ao Power Automate
POWER_AUTOMATE_SIGNATURE=your-signature-key-here

# Chave secreta (obrigatória)
# Header 'secretkey' para autenticação com Power Automate
=your-secret-key-here
```

### Configuração no Azure DevOps

Adicione as variáveis nas Pipeline Variables:
1. Vá para **Pipelines** → **Variables**
2. Clique em **New variable**
3. Adicione cada uma das 3 variáveis acima
4. Marque **Keep this value secret** para as credenciais

No arquivo `.env` (local):
```dotenv
POWER_AUTOMATE_URL=https://your-environment.e8.environment.api.powerplatform.com/...
POWER_AUTOMATE_SIGNATURE=your-signature-key-here
=your-secret-key-here
```

---

## Configurações (secrets)

Validação em `e42_evaluation.py`:

```python
import os

# Carregadas de variáveis de ambiente (Azure ou .env)
POWER_AUTOMATE_URL = os.getenv("POWER_AUTOMATE_URL")
POWER_AUTOMATE_PARAMS = {
    "api-version": "1",
    "sp": "/triggers/manual/run",
    "sv": "1.0",
    "sig": os.getenv("POWER_AUTOMATE_SIGNATURE")
}
POWER_AUTOMATE_HEADERS = {
    "Content-Type": "application/json",
    "secretkey": os.getenv("")
}
```

---

## Testes

### Test cURL completo
```bash
# Avaliação completa
curl -X POST "http://localhost:8000/api/v1/e42/evaluation" \
  -H "Content-Type: application/json" \
  -d '{"user_email": "test@example.com", "identificator": "123"}'

# Apenas fraquezas
curl -X POST "http://localhost:8000/api/v1/e42/evaluation/weaknesses-only" \
  -H "Content-Type: application/json" \
  -d '{"user_email": "test@example.com", "identificator": "123"}'
```

## Próximos Passos

1. **Banco de Dados**: A API não persiste dados no banco (coluna `e42_evaluations` foi removida)
2. **IA Plano de Ação**: Usar endpoint `/api/v1/chat/question` com weaknesses para gerar plano
3. **Dashboard**: Mostrar avaliações salvas em dashboard de RH
4. **Histórico**: Guardar múltiplas avaliações por data
5. **Comparativo**: Comparar avaliações ao longo do tempo

