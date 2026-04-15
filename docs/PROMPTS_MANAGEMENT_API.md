# Prompts Management API

**Data**: 23 de Fevereiro de 2026  
**Versão**: 1.0  
**Status**: ✅ Completo  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Conceitos Fundamentais](#conceitos-fundamentais)
3. [Endpoints](#endpoints)
4. [Modelos de Dados](#modelos-de-dados)
5. [Exemplos de Uso](#exemplos-de-uso)
6. [Sincronização com LLM Server](#sincronização-com-llm-server)
7. [Fluxos Principais](#fluxos-principais)
8. [Tratamento de Erros](#tratamento-de-erros)
9. [Variáveis de Ambiente](#variáveis-de-ambiente)

---

## Visão Geral

A **Prompts Management API** fornece funcionalidades para:
- ✅ Criar prompts customizados para cada agente
- ✅ Atualizar prompts com controle de versão
- ✅ Listar todos os prompts do sistema
- ✅ Deletar prompts (soft delete)
- ✅ Sincronizar automaticamente com o LLM Server
- ✅ Rastrear versões de prompts

### Autenticação

Todos os endpoints requerem um usuário autenticado via Azure Entra ID (MSAL).

**Autorização por Operação**:
- `GET /prompts` e `GET /prompts/{agente}`: Qualquer usuário autenticado
- `POST /prompts`: Apenas admins
- `PUT /prompts/{agente}`: Apenas admins  
- `DELETE /prompts/{agente}`: Apenas admins

### Agentes Disponíveis

| Agente | Descrição |
|--------|-----------|
| `LUZ` | Agente principal - IA para chat geral |
| `IGP` | Agente especializado - Domínio específico |
| `SMART` | Agente inteligente - Processamento avançado |

---

## Conceitos Fundamentais

### Prompt

Um **Prompt** é um template de instrução para o LLM que define como o agente deve comportar-se. Cada agente tem um prompt único.

**Estrutura**:
```json
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Você é um assistente inteligente...",
  "version": 1,
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:00:00"
}
```

**Características**:
- Um prompt por agente (unicidade por agente)
- Versionamento automático a cada atualização
- Sincronização automática com LLM Server
- Histórico de alterações com timestamps

### System Prompt

O **system_prompt** é a instrução principal que orientará o comportamento do LLM. Exemplos:

```
"Você é um assistente especializado em documentos de RH. 
Responda perguntas sobre políticas de benefícios, férias, 
admissão e folha de pagamento com base nos documentos fornecidos.
Seja conciso e profissional."
```

```
"Você é um especialista em gestão empresarial. 
Analise documentos internos e forneça insights estratégicos.
Considere o contexto organizacional e refira-se aos dados fornecidos."
```

### Versionamento

O sistema rastreia automaticamente versões de prompts:
- Versão inicial: `1`
- A cada atualização: versão incrementa (2, 3, 4, etc.)
- O campo `updated_at` registra quando foi alterado

---

## Endpoints

### Base URL
```
POST   /api/v1/prompts
GET    /api/v1/prompts
GET    /api/v1/prompts/{agente}
PUT    /api/v1/prompts/{agente}
DELETE /api/v1/prompts/{agente}
```

---

### 1. Criar Novo Prompt

**Endpoint**:
```
POST /api/v1/prompts
```

**Autenticação**: ✅ Requerida (admin)

**Request Body**:
```json
{
  "agente": "LUZ",
  "system_prompt": "Você é um assistente de RH especializado em benefícios e políticas..."
}
```

**Parâmetros**:
- `agente` (string, obrigatório): Agente para o qual criar o prompt (`LUZ`, `IGP`, `SMART`)
- `system_prompt` (string, obrigatório): Texto do prompt para o LLM

**Respostas**:

✅ **201 Created**:
```json
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Você é um assistente de RH especializado...",
  "version": 1,
  "created_at": "2026-02-23T10:30:00",
  "updated_at": "2026-02-23T10:30:00"
}
```

❌ **400 Bad Request**: Agente inválido ou prompt já existe
```json
{
  "detail": "Agente inválido: UNKNOWN. Agentes válidos: LUZ, IGP, SMART"
}
```

```json
{
  "detail": "Prompt para agente 'LUZ' já existe"
}
```

❌ **403 Forbidden**: Usuário não é admin

❌ **502 Bad Gateway**: Erro ao sincronizar com LLM Server
```json
{
  "detail": "Erro ao atualizar prompt no LLM Server: connection timeout"
}
```

---

### 2. Listar Todos os Prompts

**Endpoint**:
```
GET /api/v1/prompts
```

**Autenticação**: ✅ Requerida

**Respostas**:

✅ **200 OK**:
```json
[
  {
    "prompt_id": 1,
    "agente": "LUZ",
    "system_prompt": "Você é um assistente de RH...",
    "version": 1,
    "created_at": "2026-02-20T10:30:00",
    "updated_at": "2026-02-20T10:30:00"
  },
  {
    "prompt_id": 2,
    "agente": "IGP",
    "system_prompt": "Você é um especialista em gestão...",
    "version": 2,
    "created_at": "2026-02-20T11:00:00",
    "updated_at": "2026-02-23T14:15:00"
  },
  {
    "prompt_id": 3,
    "agente": "SMART",
    "system_prompt": "Você é um assistente avançado...",
    "version": 1,
    "created_at": "2026-02-22T09:45:00",
    "updated_at": "2026-02-22T09:45:00"
  }
]
```

❌ **401 Unauthorized**: Usuário não autenticado

---

### 3. Obter Prompt por Agente

**Endpoint**:
```
GET /api/v1/prompts/{agente}
```

**Autenticação**: ✅ Requerida

**Path Parameters**:
- `agente` (string): Nome do agente (`LUZ`, `IGP`, `SMART`)

**Respostas**:

✅ **200 OK**:
```json
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Você é um assistente de RH especializado em benefícios...",
  "version": 1,
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-20T10:30:00"
}
```

❌ **404 Not Found**: Prompt para o agente não encontrado
```json
{
  "detail": "Prompt para agente 'UNKNOWN' não encontrado"
}
```

❌ **401 Unauthorized**: Usuário não autenticado

---

### 4. Atualizar Prompt

**Endpoint**:
```
PUT /api/v1/prompts/{agente}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `agente` (string): Nome do agente (`LUZ`, `IGP`, `SMART`)

**Request Body**:
```json
{
  "system_prompt": "Novo texto do prompt com instruções atualizadas..."
}
```

**Parâmetros**:
- `system_prompt` (string, obrigatório): Novo texto do prompt

**Fluxo**:
1. Valida o agente
2. **Sincroniza com LLM Server** (PUT request)
3. Se sincronização falhar → ❌ retorna erro, não atualiza DB
4. Se sucesso → atualiza versão no DB e retorna prompt atualizado

**Respostas**:

✅ **200 OK**:
```json
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Novo texto do prompt com instruções atualizadas...",
  "version": 2,
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:00:00"
}
```

❌ **400 Bad Request**: Agente inválido
```json
{
  "detail": "Agente inválido: UNKNOWN. Agentes válidos: LUZ, IGP, SMART"
}
```

❌ **404 Not Found**: Prompt não encontrado
```json
{
  "detail": "Prompt para agente 'LUZ' não encontrado"
}
```

❌ **403 Forbidden**: Usuário não é admin

❌ **502 Bad Gateway**: Erro ao sincronizar com LLM Server
```json
{
  "detail": "Erro ao atualizar prompt no LLM Server: <erro específico>"
}
```

---

### 5. Deletar Prompt

**Endpoint**:
```
DELETE /api/v1/prompts/{agente}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `agente` (string): Nome do agente (`LUZ`, `IGP`, `SMART`)

**Respostas**:

✅ **204 No Content**: Prompt deletado com sucesso

❌ **404 Not Found**: Prompt não encontrado
```json
{
  "detail": "Prompt para agente 'LUZ' não encontrado"
}
```

❌ **403 Forbidden**: Usuário não é admin

---

## Modelos de Dados

### PromptResponse
```python
{
  "prompt_id": int
  "agente": str            # LUZ, IGP, SMART
  "system_prompt": str     # Texto do prompt
  "version": int           # Controle de versão
  "created_at": datetime
  "updated_at": datetime
}
```

### PromptCreate
```python
{
  "agente": str            # Obrigatório
  "system_prompt": str     # Obrigatório
}
```

### PromptUpdate
```python
{
  "system_prompt": str     # Obrigatório
}
```

---

## Exemplos de Uso

### cURL

#### 1. Criar novo prompt
```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agente": "LUZ",
    "system_prompt": "Você é um assistente especializado em documentos de RH. Responda perguntas sobre políticas de benefícios e férias baseado nos documentos fornecidos."
  }'
```

#### 2. Listar todos os prompts
```bash
curl -X GET http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>"
```

#### 3. Obter prompt de um agente específico
```bash
curl -X GET http://localhost:8000/api/v1/prompts/LUZ \
  -H "Authorization: Bearer <token>"
```

#### 4. Atualizar prompt
```bash
curl -X PUT http://localhost:8000/api/v1/prompts/LUZ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Versão 2: Você é um assistente de RH com experiência em processos de admissão..."
  }'
```

#### 5. Deletar prompt
```bash
curl -X DELETE http://localhost:8000/api/v1/prompts/IGP \
  -H "Authorization: Bearer <token>"
```

### Python

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer <token>", "Content-Type": "application/json"}

# Criar novo prompt para LUZ
response = requests.post(
    f"{BASE_URL}/prompts",
    headers=HEADERS,
    json={
        "agente": "LUZ",
        "system_prompt": """Você é um assistente inteligente de RH.
        Responda perguntas sobre:
        - Benefícios e folha de pagamento
        - Políticas de férias e ausências
        - Processos de admissão
        Sempre baseie suas respostas nos documentos fornecidos."""
    }
)
prompt = response.json()
print(f"Prompt criado para {prompt['agente']}: versão {prompt['version']}")

# Listar todos os prompts
response = requests.get(f"{BASE_URL}/prompts", headers=HEADERS)
all_prompts = response.json()
for p in all_prompts:
    print(f"{p['agente']}: versão {p['version']} (updated: {p['updated_at']})")

# Obter prompt específico
response = requests.get(f"{BASE_URL}/prompts/LUZ", headers=HEADERS)
luz_prompt = response.json()
print(f"Prompt LUZ: {luz_prompt['system_prompt']}")

# Atualizar prompt
response = requests.put(
    f"{BASE_URL}/prompts/LUZ",
    headers=HEADERS,
    json={
        "system_prompt": "Versão melhorada com mais contexto..."
    }
)
updated = response.json()
print(f"Atualizado para versão {updated['version']}")

# Deletar prompt
response = requests.delete(
    f"{BASE_URL}/prompts/IGP",
    headers=HEADERS
)
print(f"Deletado: {response.status_code}")
```

### JavaScript/TypeScript

```typescript
const baseUrl = "http://localhost:8000/api/v1";
const headers = {
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Criar prompt
const createResponse = await fetch(`${baseUrl}/prompts`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    agente: "SMART",
    system_prompt: "Você é um assistente avançado especializado em análise de dados..."
  })
});
const prompt = await createResponse.json();
console.log(`Prompt criado: ${prompt.agente} v${prompt.version}`);

// Listar prompts
const listResponse = await fetch(`${baseUrl}/prompts`, { headers });
const prompts = await listResponse.json();
prompts.forEach(p => {
  console.log(`${p.agente}: v${p.version} - Criado: ${p.created_at}`);
});

// Atualizar prompt
const updateResponse = await fetch(`${baseUrl}/prompts/SMART`, {
  method: "PUT",
  headers,
  body: JSON.stringify({
    system_prompt: "Versão 2 com instruções melhoradas..."
  })
});
const updated = await updateResponse.json();
console.log(`Atualizado para versão ${updated.version}`);

// Deletar prompt
const deleteResponse = await fetch(`${baseUrl}/prompts/IGP`, {
  method: "DELETE",
  headers
});
console.log(`Deletado: ${deleteResponse.status}`);
```

---

## Sincronização com LLM Server

### Fluxo de Sincronização

A API implementa um fluxo **fail-safe** para sincronização com o LLM Server:

```
1. Validar agente
   │
2. Sincronizar com LLM Server
   ├─ Se FALHA → ❌ Retorna erro (código 502)
   │               DB não é alterado
   │
   └─ Se SUCESSO → Continua
        │
        v
3. Atualizar versão no DB
        │
        v
4. Retornar prompt atualizado
```

### Requisições ao LLM Server

#### Para Criar Prompt
```
PUT /api/v1/agents/{agente}/prompts
{
  "system_prompt": "...",
  "version": 1
}
```

#### Para Atualizar Prompt
```
PUT /api/v1/agents/{agente}/prompts
{
  "system_prompt": "...",
  "version": 2
}
```

### Retry Logic

O sistema implementa retry automático com backoff exponencial:

```python
# Configuração
LLM_SERVER_MAX_RETRIES = 3
LLM_SERVER_RETRY_DELAY = 1 (segundo)

# Tentativas
Tentativa 1: após 1s
Tentativa 2: após 2s
Tentativa 3: após 4s
```

---

## Fluxos Principais

### Fluxo 1: Criar Prompt para Novo Agente

```
┌─────────────────────┐
│ Admin autenticado   │
└──────────┬──────────┘
           │
           v
┌────────────────────────┐
│ POST /api/v1/prompts   │
│ agente: LUZ            │
│ system_prompt: "..."   │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Validar agente é       │
│ válido (LUZ/IGP/SMART) │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Verificar se prompt    │
│ já existe para agente  │
└──────────┬─────────────┘
           │ (não existe)
           v
┌────────────────────────┐
│ Sincronizar com        │
│ LLM Server (PUT)       │
└──────────┬─────────────┘
           │ (sucesso)
           v
┌────────────────────────┐
│ INSERT no DB           │
│ versão=1               │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Retornar PromptResponse│
│ 201 Created            │
└────────────────────────┘
```

### Fluxo 2: Atualizar Prompt Existente

```
┌─────────────────────┐
│ Admin autenticado   │
└──────────┬──────────┘
           │
           v
┌──────────────────────────┐
│ PUT /api/v1/prompts/LUZ  │
│ system_prompt: "v2..."   │
└──────────┬───────────────┘
           │
           v
┌────────────────────────┐
│ Buscar prompt atual    │
│ (SELECT version FROM…) │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Incrementar versão     │
│ 1 -> 2                 │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Sincronizar com        │
│ LLM Server (PUT v2)    │
└──────────┬─────────────┘
           │ (se falha)
           ├─→ ❌ Erro 502
           │  DB não toca
           │
           │ (se sucesso)
           v
┌────────────────────────┐
│ UPDATE no DB           │
│ nova versão e          │
│ system_prompt          │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ Retornar PromptResponse│
│ 200 OK                 │
└────────────────────────┘
```

### Fluxo 3: Recuperação de Falha (LLM Server Down)

```
┌──────────────────────┐
│ LLM Server está DOWN │
└──────┬───────────────┘
       │
       v
┌──────────────────────────┐
│ Cliente tenta atualizar  │
│ prompt                   │
└──────┬───────────────────┘
       │
       v
┌──────────────────────────┐
│ Sincronizar falha        │
│ (connection timeout)     │
└──────┬───────────────────┘
       │
       v
┌──────────────────────────┐
│ Retry automático até 3x  │
│ (backoff exponencial)    │
└──────┬───────────────────┘
       │
       ├─ Tentativa 1: ❌
       ├─ Tentativa 2: ❌
       └─ Tentativa 3: ❌
             │
             v
      ┌──────────────┐
      │ ❌ Erro 502  │
      │ DB não       │
      │ modificado   │
      └──────────────┘
```

---

## Tratamento de Erros

### 400 Bad Request

**Causas**:
- Agente inválido (UNKNOWN, INVALID, etc)
- Prompt já existe para o agente
- JSON malformado

**Exemplo**:
```json
{
  "detail": "Agente inválido: TESTING. Agentes válidos: LUZ, IGP, SMART"
}
```

### 401 Unauthorized

**Causa**: Token JWT ausente ou inválido

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

**Causa**: Usuário autenticado mas não é admin (para POST/PUT/DELETE)

```json
{
  "detail": "Usuário não tem permissão para operações de admin"
}
```

### 404 Not Found

**Causa**: Prompt não encontrado

```json
{
  "detail": "Prompt para agente 'LUZ' não encontrado"
}
```

### 502 Bad Gateway

**Causa**: Erro ao sincronizar com LLM Server (conexão, timeout, erro remoto)

```json
{
  "detail": "Erro ao atualizar prompt no LLM Server: <detalhes do erro>"
}
```

**Ações recomendadas**:
1. Verificar se LLM Server está online
2. Validar URL de LLM_SERVER_URL
3. Verificar conectividade de rede
4. Tentar novamente (sistema faz retry automático 3x)

### 500 Internal Server Error

**Causa**: Erro genérico no servidor ou banco de dados

```json
{
  "detail": "Erro ao criar prompt: <erro específico>"
}
```

---

## Variáveis de Ambiente

### Configuração do LLM Server

```bash
# URL do LLM Server
LLM_SERVER_URL=http://localhost:8001

# Timeout para requisições (segundos)
LLM_SERVER_TIMEOUT=30

# Número máximo de tentativas de retry
LLM_SERVER_MAX_RETRIES=3

# Delay inicial para retry em segundos (backoff exponencial)
LLM_SERVER_RETRY_DELAY=1
```

### Aplicação

No arquivo `.env`:
```env
LLM_SERVER_URL=http://llm-server:8001
LLM_SERVER_TIMEOUT=30
LLM_SERVER_MAX_RETRIES=3
LLM_SERVER_RETRY_DELAY=1
```

No arquivo `docker-compose.yml`:
```yaml
services:
  api:
    environment:
      LLM_SERVER_URL: http://llm-server:8001
      LLM_SERVER_TIMEOUT: 30
      LLM_SERVER_MAX_RETRIES: 3
      LLM_SERVER_RETRY_DELAY: 1
    depends_on:
      - llm-server
```

---

## Database Schema

### Tabela `prompts`
```sql
CREATE TABLE prompts (
  prompt_id INT PRIMARY KEY IDENTITY(1,1),
  agente VARCHAR(50) UNIQUE NOT NULL,
  system_prompt TEXT NOT NULL,
  version INT DEFAULT 1,
  created_at DATETIME DEFAULT GETUTCDATE(),
  updated_at DATETIME DEFAULT GETUTCDATE()
);

-- Índices
CREATE UNIQUE INDEX idx_prompts_agente ON prompts(agente);
CREATE INDEX idx_prompts_created_at ON prompts(created_at);
```

### Exemplos de Dados

```sql
INSERT INTO prompts (agente, system_prompt, version, created_at, updated_at) VALUES
('LUZ', 'Você é um assistente de RH...', 1, GETUTCDATE(), GETUTCDATE()),
('IGP', 'Você é um especialista em gestão...', 1, GETUTCDATE(), GETUTCDATE()),
('SMART', 'Você é um assistente avançado...', 1, GETUTCDATE(), GETUTCDATE());
```

---

## Melhores Práticas

### 1. Validar antes de Atualizar

**❌ Não faça**:
```python
# Não envie textos muito longos
requests.put(f"/api/v1/prompts/LUZ", 
  json={"system_prompt": "..." * 10000})  # Muito grande
```

**✅ Faça**:
```python
# Valide tamanho e qualidade antes
prompt_text = "Você é um assistente..."
if len(prompt_text) > 50000:
    raise ValueError("Prompt muito longo")
requests.put(f"/api/v1/prompts/LUZ", 
  json={"system_prompt": prompt_text})
```

### 2. Lidar com Sincronização Falhando

**❌ Evite**:
```python
# Não ignore erros de sincronização
try:
    requests.put(f"/api/v1/prompts/LUZ", json={...})
except Exception:
    pass  # Ignorar erro
```

**✅ Faça**:
```python
# Retente e log
import time
max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.put(f"/api/v1/prompts/LUZ", 
          json={...}, timeout=30)
        if response.status_code == 200:
            print("Prompt atualizado com sucesso")
            break
    except Exception as e:
        print(f"Tentativa {attempt+1} falhou: {e}")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Backoff exponencial
```

### 3. Logging e Auditoria

**✅ Sempre log**:
```python
logger.info(f"Admin {admin_email} alterou prompt do agente {agente}")
logger.info(f"Prompt {agente} atualizado: v{old_version} -> v{new_version}")
logger.info(f"Novo prompt_id: {prompt['prompt_id']}")
```

### 4. Versionamento

**Observe**:
- Cada atualização incrementa a versão automaticamente
- O histórico de versões fica no DB (com timestamps)
- Use `updated_at` para rastrear quando foi mudado

### 5. Documentar Mudanças

Considere adicionar um campo de changelog (implementação futura):

```
v1: Prompt inicial
v2: Adicionado contexto sobre benefícios
v3: Melhorado tratamento de datas
```

---

## Exemplos Completos de Prompts

### LUZ - RH Assistant
```
Você é um assistente inteligente especializado em Recursos Humanos (RH).

Sua responsabilidade é responder perguntas sobre:
- Políticas de benefícios (vale-refeição, vale-transporte, etc.)
- Folha de pagamento e remuneração
- Férias, licenças e ausências
- Admissão e onboarding
- Programas de desenvolvimento
- Segurança e conformidade

IMPORTANTE:
- Sempre baseie suas respostas apenas nos documentos fornecidos
- Se uma informação não estiver nos documentos, diga "Esta informação não está disponível nos documentos"
- Seja conciso, profissional e empático
- Use linguagem clara e simples

Documentos disponíveis: Políticas de RH, Manual de Benefícios, Tabela Salarial
```

### IGP - Business Analyst
```
Você é um especialista em análise de gestão empresarial e processos.

Sua responsabilidade é:
- Analisar documentos de negócio (estratégia, processos, procedimentos)
- Fornecer insights sobre eficiência operacional
- Identificar gargalos e oportunidades de melhoria
- Propor soluções baseadas em práticas consolidadas
- Gerar relatórios executivos claros

IMPORTANTE:
- Contextualize as análises no cenário organizacional
- Sempre cite os dados e evidências dos documentos
- Evite recomendações genéricas
- Mantenha tom profissional e consultivo
```

### SMART - Advanced AI
```
Você é um assistente inteligente avançado com especialização em processamento de dados complexos.

Sua responsabilidade é:
- Análise profunda de documentos estruturados e não-estruturados
- Síntese de informações de múltiplas fontes
- Extração de padrões e correlações
- Geração de respostas semanticamente precisas
- Tratamento de consultas complexas e multi-facetadas

IMPORTANTE:
- Use raciocínio lógico estruturado
- Mencione confiança e limitações de análise
- Cite fontes dos documentos
- Adapte profundidade de resposta à complexidade da pergunta
```

---

## Troubleshooting

### "Erro ao sincronizar com LLM Server"

**Causa 1: LLM Server offline**
```bash
# Verificar se está rodando
curl http://localhost:8001/health

# Se timeout, reiniciar
docker restart llm-server
```

**Causa 2: URL incorreta**
```bash
# Validar .env
echo $LLM_SERVER_URL

# Corrigir se necessário
export LLM_SERVER_URL=http://llm-server:8001
```

### "Prompt já existe"

```python
# Verificar se existe
response = requests.get(f"/api/v1/prompts/LUZ", headers=headers)
if response.status_code == 200:
    print("Prompt existe, use PUT para atualizar")
else:
    print("Não existe, pode criar")
```

### "Agente inválido"

```python
# Verificar agentes disponíveis
response = requests.get("/api/v1/admins/allowed-agents", headers=headers)
valid_agents = [a["code"] for a in response.json()["agents"]]
print(f"Agentes válidos: {valid_agents}")
```

---

## Roadmap Futuro

- [ ] Endpoint para obter histórico de versões
- [ ] Rollback para versão anterior
- [ ] Templates pré-configurados de prompts
- [ ] Testes A/B de prompts
- [ ] Métricas de efetividade de prompts
- [ ] Backup automático de prompts

---

## Versionamento da API

- **Versão Atual**: 1.0
- **Data da última atualização**: 23 de Fevereiro de 2026
- **Status**: Produção
- **Suporte**: LLM Server v1.0+
